"""
Mostly AI generated to be easy to test RTSP, otherwise it's a little hard to have an RTSP
It uses same video but through RTSP
"""
import ffmpeg
import sys
import os
import pyperclip


def stream_to_rtsp(input_file: str, output_url: str, realtime: bool = True) -> None:
    """
    Streams a video file to an RTSP server using H.264/AAC.
    Automatically converts formats for compatibility.
    """

    if not os.path.exists(input_file):
        print(f"[ERROR] Input file does not exist: {input_file}")
        sys.exit(1)

    print(f"[INFO] Starting stream...")
    print(f"       Input : {input_file}")
    print(f"       Output: {output_url}")


    rtsp_url = "rtsp://localhost:8555/live"
    pyperclip.copy(rtsp_url)

    print("RTSP URL copied to clipboard!")

    # FFmpeg input options
    input_opts = {}
    if realtime:
        # -re reads the input at real-time speed (ideal for streaming)
        input_opts["re"] = None

    try:
        (
            ffmpeg
            .input(input_file, **input_opts)
            .output(
                output_url,
                vcodec="libx264",
                acodec="aac",
                preset="veryfast",
                tune="zerolatency",
                pix_fmt="yuv420p",
                format="rtsp",
                r=30,
                bufsize="1000k",
                **{"rtsp_transport": "tcp"},  # more stable for most players/servers
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        print("[INFO] Streaming completed successfully.")

    except ffmpeg.Error as e:
        print("[ERROR] FFmpeg encountered an error.")
        print(e.stderr.decode("utf-8"))
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] FFmpeg executable not found. Ensure it is installed and in PATH.")
        sys.exit(1)


if __name__ == "__main__":
    input_video_path = "video.webm"
    output_stream_url = "rtsp://localhost:8555/live"

    stream_to_rtsp(input_video_path, output_stream_url)
