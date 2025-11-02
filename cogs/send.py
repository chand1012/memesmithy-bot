import tempfile
from pathlib import Path

import httpx
import nextcord
from nextcord.ext import commands
import yt_dlp


class Send(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Discord file size limit is 25MB, but we want to enforce 8MB
        self.MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB in bytes

    def _is_video_url(self, url: str) -> bool:
        """Check if URL is likely a video platform."""
        video_domains = [
            "youtube.com",
            "youtu.be",
            "vimeo.com",
            "tiktok.com",
            "instagram.com",
            "twitter.com",
            "x.com",
            "reddit.com",
        ]
        return any(domain in url.lower() for domain in video_domains)

    async def _download_with_ytdlp(self, url: str, temp_dir: Path) -> Path | None:
        """Download media using yt-dlp for video platforms."""
        ydl_opts = {
            "outtmpl": str(temp_dir / "%(title)s.%(ext)s"),
            "format": "best[filesize<8M]/best",  # Prefer formats under 8MB
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to check file size
                info = ydl.extract_info(url, download=False)

                # Check if we can get file size from info
                if "filesize" in info or "filesize_approx" in info:
                    size = info.get("filesize") or info.get("filesize_approx")
                    if size and size > self.MAX_FILE_SIZE:
                        return None

                # Download the file
                ydl.download([url])

                # Find the downloaded file
                for file in temp_dir.iterdir():
                    if file.is_file():
                        if file.stat().st_size > self.MAX_FILE_SIZE:
                            file.unlink()
                            return None
                        return file
        except Exception as e:
            print(f"Error downloading with yt-dlp: {e}")
            return None

        return None

    async def _download_direct_media(self, url: str, temp_dir: Path) -> Path | None:
        """Download media directly via HTTP for direct media links."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First, check the file size via HEAD request
                head_response = await client.head(url, follow_redirects=True)

                # Get content length if available
                content_length = head_response.headers.get("Content-Length")
                if content_length:
                    size = int(content_length)
                    if size > self.MAX_FILE_SIZE:
                        return None

                # Download the file
                async with client.stream("GET", url, follow_redirects=True) as response:
                    response.raise_for_status()

                    # Get filename from URL or Content-Disposition header
                    filename = (
                        response.headers.get("Content-Disposition", "")
                        .split("filename=")[-1]
                        .strip('"')
                        if "filename="
                        in response.headers.get("Content-Disposition", "")
                        else None
                    )

                    if not filename:
                        # Extract from URL
                        filename = url.split("/")[-1].split("?")[0]
                        if not filename or "." not in filename:
                            filename = "media_file"  # Default name

                    filepath = temp_dir / filename

                    # Download with size check
                    total_size = 0
                    with open(filepath, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            total_size += len(chunk)
                            if total_size > self.MAX_FILE_SIZE:
                                if filepath.exists():
                                    filepath.unlink()
                                return None
                            f.write(chunk)

                    # Final size check
                    if (
                        filepath.exists()
                        and filepath.stat().st_size > self.MAX_FILE_SIZE
                    ):
                        filepath.unlink()
                        return None

                    return filepath
        except Exception as e:
            print(f"Error downloading direct media: {e}")
            return None

    @nextcord.slash_command(
        name="send",
        description="Download and send media from a URL to the channel. Max 8MB.",
    )
    async def send(
        self,
        interaction: nextcord.Interaction,
        url: str = nextcord.SlashOption(
            name="url",
            description="URL to the video or media file",
            required=True,
        ),
    ):
        """Download media from a URL and send it to the channel."""
        # Defer response since download might take time
        await interaction.response.defer()

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Determine download method
            if self._is_video_url(url):
                file_path = await self._download_with_ytdlp(url, temp_path)
            else:
                file_path = await self._download_direct_media(url, temp_path)

            if not file_path or not file_path.exists():
                await interaction.followup.send(
                    "❌ Sorry, but the media needs to be less than 8MB.",
                    ephemeral=True,
                )
                return

            # Send the file
            try:
                file = nextcord.File(file_path, filename=file_path.name)
                await interaction.followup.send(file=file)
            except Exception as e:
                await interaction.followup.send(
                    f"❌ Error sending file: {str(e)}", ephemeral=True
                )
            # File will be automatically deleted when temp_dir context exits
