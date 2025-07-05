import customtkinter as ctk
from pytubefix import YouTube, Playlist
from pytubefix.cli import on_progress
import os
import threading
from tkinter import filedialog
import time


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Simple YouTube Downloader")
        self.geometry("1280x960")
        ctk.set_appearance_mode("dark")

        # Initialize variables
        self.link = ctk.StringVar()
        self.download_mode = ctk.StringVar(value="audio")  # audio or video
        self.source_type = ctk.StringVar(value="single")  # single or playlist
        self.download_path = os.path.abspath("downloads")  # Default download path

        # Progress tracking variables
        self.download_start_time = 0
        self.last_bytes_downloaded = 0
        self.last_time_check = 0
        self.current_file_name = ""

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main frames
        self.create_control_panel()
        self.create_main_content()

    def create_control_panel(self):
        # Control panel frame (left side)
        self.control_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.control_frame.grid_propagate(False)

        # Control panel title
        control_title = ctk.CTkLabel(
            self.control_frame,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        control_title.pack(pady=(20, 30))

        # Download mode selection
        mode_label = ctk.CTkLabel(
            self.control_frame,
            text="Download Mode:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        mode_label.pack(pady=(0, 10))

        self.mode_audio_radio = ctk.CTkRadioButton(
            self.control_frame,
            text="Audio Only (MP3)",
            variable=self.download_mode,
            value="audio",
            command=self.on_mode_change,
        )
        self.mode_audio_radio.pack(pady=5, padx=20, anchor="w")

        self.mode_video_radio = ctk.CTkRadioButton(
            self.control_frame,
            text="Video (MP4)",
            variable=self.download_mode,
            value="video",
            command=self.on_mode_change,
        )
        self.mode_video_radio.pack(pady=5, padx=20, anchor="w")

        # Source type selection
        source_label = ctk.CTkLabel(
            self.control_frame,
            text="Source Type:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        source_label.pack(pady=(30, 10))

        self.source_single_radio = ctk.CTkRadioButton(
            self.control_frame,
            text="Single Video",
            variable=self.source_type,
            value="single",
            command=self.on_source_change,
        )
        self.source_single_radio.pack(pady=5, padx=20, anchor="w")

        self.source_playlist_radio = ctk.CTkRadioButton(
            self.control_frame,
            text="Playlist",
            variable=self.source_type,
            value="playlist",
            command=self.on_source_change,
        )
        self.source_playlist_radio.pack(pady=5, padx=20, anchor="w")

        # Download location info
        location_label = ctk.CTkLabel(
            self.control_frame,
            text="Download Location:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        location_label.pack(pady=(30, 10))

        # Frame for location display and button
        location_frame = ctk.CTkFrame(self.control_frame)
        location_frame.pack(pady=5, padx=20, fill="x")

        self.location_info = ctk.CTkLabel(
            location_frame,
            text=self.download_path,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=250,
            justify="left",
        )
        self.location_info.pack(pady=(10, 5), padx=10, fill="x")

        # Button to change download location
        self.change_location_btn = ctk.CTkButton(
            location_frame,
            text="Change Folder",
            command=self.change_download_location,
            width=200,
            height=30,
            font=ctk.CTkFont(size=12),
        )
        self.change_location_btn.pack(pady=(0, 10), padx=10)

    def create_main_content(self):
        # Main content frame (right side)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Title
        main_title = ctk.CTkLabel(
            self.main_frame,
            text="Simple YouTube Downloader",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        main_title.grid(row=0, column=0, pady=(30, 20), sticky="ew")

        # Input section
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_label = ctk.CTkLabel(
            self.input_frame,
            text="Paste your YouTube link here:",
            font=ctk.CTkFont(size=16),
        )
        self.input_label.pack(pady=(20, 10))

        self.link_entry = ctk.CTkEntry(
            self.input_frame,
            textvariable=self.link,
            width=600,
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self.link_entry.pack(pady=10, padx=20)

        self.download_btn = ctk.CTkButton(
            self.input_frame,
            text="Download",
            command=self.start_download,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.download_btn.pack(pady=20)

        # Status and progress section
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(10, 30))
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(2, weight=1)

        status_title = ctk.CTkLabel(
            self.status_frame,
            text="Download Status",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        status_title.grid(row=0, column=0, pady=(20, 10), sticky="ew")

        # Progress information frame
        self.progress_info_frame = ctk.CTkFrame(self.status_frame)
        self.progress_info_frame.grid(
            row=1, column=0, sticky="ew", padx=20, pady=(0, 10)
        )
        self.progress_info_frame.grid_columnconfigure(0, weight=1)

        # Current file label
        self.current_file_label = ctk.CTkLabel(
            self.progress_info_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        )
        self.current_file_label.grid(row=0, column=0, pady=(15, 5), sticky="ew")

        # Individual file progress
        file_progress_label = ctk.CTkLabel(
            self.progress_info_frame,
            text="Current File Progress:",
            font=ctk.CTkFont(size=12),
        )
        file_progress_label.grid(row=1, column=0, pady=(5, 2), sticky="w", padx=10)

        self.file_progress_bar = ctk.CTkProgressBar(self.progress_info_frame, width=600)
        self.file_progress_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.file_progress_bar.set(0)

        # File progress info (speed, time, percentage)
        self.file_progress_info = ctk.CTkLabel(
            self.progress_info_frame,
            text="0% • 0 MB/s • --:-- remaining",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.file_progress_info.grid(row=3, column=0, pady=(0, 5), sticky="ew")

        # Overall progress (for playlists)
        overall_progress_label = ctk.CTkLabel(
            self.progress_info_frame,
            text="Overall Progress:",
            font=ctk.CTkFont(size=12),
        )
        overall_progress_label.grid(row=4, column=0, pady=(10, 2), sticky="w", padx=10)

        self.overall_progress_bar = ctk.CTkProgressBar(
            self.progress_info_frame, width=600
        )
        self.overall_progress_bar.grid(
            row=5, column=0, sticky="ew", padx=10, pady=(0, 5)
        )
        self.overall_progress_bar.set(0)

        # Overall progress info
        self.overall_progress_info = ctk.CTkLabel(
            self.progress_info_frame,
            text="0 of 0 files completed",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.overall_progress_info.grid(row=6, column=0, pady=(0, 15), sticky="ew")

        # Scrollable text widget for status messages
        self.status_text = ctk.CTkTextbox(
            self.status_frame, width=600, height=300, font=ctk.CTkFont(size=12)
        )
        self.status_text.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Initial status
        self.add_status_message("Ready to download")

    def change_download_location(self):
        new_path = filedialog.askdirectory(
            title="Select Download Directory", initialdir=self.download_path
        )

        if new_path:  # User selected a directory
            self.download_path = new_path
            self.location_info.configure(text=self.download_path)
            self.add_status_message(
                f"📁 Download location changed to: {self.download_path}"
            )

    def on_mode_change(self):
        mode = self.download_mode.get()
        if mode == "audio":
            self.add_status_message("Mode changed to: Audio Only (MP3)")
        else:
            self.add_status_message("Mode changed to: Video (MP4)")

    def on_source_change(self):
        source = self.source_type.get()
        # Clear the input field when switching source types
        self.link.set("")

        if source == "single":
            self.input_label.configure(text="Paste your YouTube link here:")
            self.add_status_message("Source changed to: Single Video")
        else:
            self.input_label.configure(text="Paste your YouTube playlist link here:")
            self.add_status_message("Source changed to: Playlist")

    def add_status_message(self, message):
        self.status_text.insert("end", f"• {message}\n")
        self.status_text.see("end")

    def start_download(self):
        # Start download in a separate thread to prevent UI freezing
        thread = threading.Thread(target=self.download_content)
        thread.daemon = True
        thread.start()

    def download_content(self):
        try:
            url = self.link.get()

            if not url:
                self.add_status_message("❌ Please enter a YouTube URL")
                return

            # Disable download button during download
            self.download_btn.configure(state="disabled")
            self.reset_progress_bars()

            # Create downloads directory if it doesn't exist
            if not os.path.exists(self.download_path):
                os.makedirs(self.download_path)
                self.add_status_message(f"📁 Created directory: {self.download_path}")

            source_type = self.source_type.get()
            download_mode = self.download_mode.get()

            if source_type == "single":
                self.download_single_video(url, download_mode)
            else:
                self.download_playlist(url, download_mode)

        except Exception as e:
            self.add_status_message(f"❌ Error: {str(e)}")
        finally:
            # Re-enable download button
            self.download_btn.configure(state="normal")
            self.reset_progress_bars()
            self.current_file_label.configure(text="Download completed!")

    def reset_progress_bars(self):
        self.file_progress_bar.set(0)
        self.overall_progress_bar.set(0)
        self.file_progress_info.configure(text="0% • 0 MB/s • --:-- remaining")
        self.overall_progress_info.configure(text="0 of 0 files completed")
        self.current_file_name = ""

    def format_bytes(self, bytes_val):
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024**2:
            return f"{bytes_val/1024:.1f} KB"
        elif bytes_val < 1024**3:
            return f"{bytes_val/(1024**2):.1f} MB"
        else:
            return f"{bytes_val/(1024**3):.1f} GB"

    def format_time(self, seconds):
        if seconds < 0 or seconds == float("inf"):
            return "--:--"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def download_single_video(self, url, mode):
        self.add_status_message(f"🔄 Starting download from: {url}")

        yt = YouTube(url, on_progress_callback=self.progress_callback)

        # Get video info
        self.add_status_message(f"📺 Title: {yt.title}")
        self.add_status_message(f"👤 Author: {yt.author}")
        self.add_status_message(f"⏱️ Duration: {yt.length} seconds")

        # Update current file display
        self.current_file_name = yt.title
        self.current_file_label.configure(text=f"Downloading: {self.current_file_name}")

        # Set overall progress for single video
        self.overall_progress_info.configure(text="1 of 1 files")
        self.overall_progress_bar.set(0)

        if mode == "audio":
            stream = yt.streams.get_audio_only()
            if not stream:
                self.add_status_message("❌ No audio stream found")
                return

            self.add_status_message("🎵 Downloading audio...")
            self.download_start_time = time.time()
            out_file = stream.download(self.download_path)
            base, ext = os.path.splitext(out_file)
            new_file = base + ".mp3"
            os.rename(out_file, new_file)
            self.add_status_message(
                f"✅ Audio downloaded: {os.path.basename(new_file)}"
            )
        else:
            stream = yt.streams.get_highest_resolution()
            if not stream:
                self.add_status_message("❌ No video stream found")
                return

            self.add_status_message("🎬 Downloading video...")
            self.download_start_time = time.time()
            out_file = stream.download(self.download_path)
            self.add_status_message(
                f"✅ Video downloaded: {os.path.basename(out_file)}"
            )

        # Complete overall progress
        self.overall_progress_bar.set(1.0)
        self.overall_progress_info.configure(text="1 of 1 files completed")

    def download_playlist(self, url, mode):
        self.add_status_message(f"🔄 Loading playlist from: {url}")

        playlist = Playlist(url)
        total_videos = len(playlist.video_urls)

        self.add_status_message(f"📋 Playlist: {playlist.title}")
        self.add_status_message(f"📊 Total videos: {total_videos}")

        # Update overall progress info
        self.overall_progress_info.configure(
            text=f"0 of {total_videos} files completed"
        )

        # Create a folder for the playlist
        playlist_folder_name = self.sanitize_filename(playlist.title)
        playlist_path = os.path.join(self.download_path, playlist_folder_name)

        if not os.path.exists(playlist_path):
            os.makedirs(playlist_path)
            self.add_status_message(
                f"📁 Created playlist folder: {playlist_folder_name}"
            )

        for i, video_url in enumerate(playlist.video_urls, 1):
            try:
                self.add_status_message(f"🔄 Downloading video {i}/{total_videos}")

                yt = YouTube(video_url, on_progress_callback=self.progress_callback)
                self.add_status_message(f"📺 {i}. {yt.title}")

                # Update current file display
                self.current_file_name = yt.title
                self.current_file_label.configure(
                    text=f"Downloading: {self.current_file_name}"
                )

                # Reset file progress for new file
                self.file_progress_bar.set(0)
                self.download_start_time = time.time()

                if mode == "audio":
                    stream = yt.streams.get_audio_only()
                    if stream:
                        out_file = stream.download(playlist_path)
                        base, ext = os.path.splitext(out_file)
                        new_file = base + ".mp3"
                        os.rename(out_file, new_file)
                        self.add_status_message(
                            f"✅ Audio downloaded: {os.path.basename(new_file)}"
                        )
                else:
                    stream = yt.streams.get_highest_resolution()
                    if stream:
                        out_file = stream.download(playlist_path)
                        self.add_status_message(
                            f"✅ Video downloaded: {os.path.basename(out_file)}"
                        )

                # Update overall progress
                overall_progress = i / total_videos
                self.overall_progress_bar.set(overall_progress)
                self.overall_progress_info.configure(
                    text=f"{i} of {total_videos} files completed"
                )

            except Exception as e:
                self.add_status_message(f"❌ Error with video {i}: {str(e)}")

        self.add_status_message(
            f"🎉 Playlist download completed! ({total_videos} videos)"
        )
        self.add_status_message(f"📁 Files saved in: {playlist_path}")

    def sanitize_filename(self, filename):
        """Remove or replace invalid characters for folder/file names"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        # Remove extra spaces and limit length
        filename = filename.strip()[:100]
        return filename

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = bytes_downloaded / total_size

        # Update file progress bar
        self.file_progress_bar.set(percentage)

        # Calculate download speed and time estimation
        current_time = time.time()
        if hasattr(self, "download_start_time") and self.download_start_time > 0:
            elapsed_time = current_time - self.download_start_time

            if elapsed_time > 0:
                # Calculate speed
                speed = bytes_downloaded / elapsed_time

                # Calculate remaining time
                if speed > 0:
                    remaining_time = bytes_remaining / speed
                else:
                    remaining_time = 0

                # Update progress info
                speed_text = f"{self.format_bytes(speed)}/s"
                time_text = self.format_time(remaining_time)
                percentage_text = f"{percentage*100:.1f}%"

                self.file_progress_info.configure(
                    text=f"{percentage_text} • {speed_text} • {time_text} remaining"
                )

        # For single files, also update overall progress
        if hasattr(self, "source_type") and self.source_type.get() == "single":
            self.overall_progress_bar.set(percentage)


if __name__ == "__main__":
    app = App()
    app.mainloop()
