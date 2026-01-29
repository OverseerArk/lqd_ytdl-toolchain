# VidGet - v0.0.1 (pre-alpha)
# Under development stage. May have bugs.

if __name__ != "__main__":
    exit(1)

# Import modules
import pygame
import pygame_gui
from pygame_gui.elements import (
    UITextEntryLine,
    UIDropDownMenu,
    UIButton,
    UILabel,
    UICheckBox,
    UIProgressBar,
    UIPanel
)
from pygame_gui.core.object_id import ObjectID

import sys, os
import webbrowser
from pathlib import Path
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue

from yt_dlp import YoutubeDL
from rich.console import Console
console = Console()

import re

if os.name != "nt":
    os.system("echo \"Error: OS unsupported.\"")
    sys.exit(1)

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(s):
    return ANSI_RE.sub('', s)


def highlight(*args):
    console.print(f"[cyan]{args}[/]")

print = highlight

thread = ThreadPoolExecutor(max_workers=1, thread_name_prefix="_vidget_dl-")
queue = Queue()


# Path resolver
def resource_path(relative_path: str | Path) -> Path:
    """
    Resolve resource paths for both normal Python and PyInstaller frozen apps.
    Returns a Path object.
    """
    relative_path = Path(relative_path)

    if getattr(sys, "frozen", False) and hasattr(sys, "#_MEIPASS"):
        # PyInstaller temp folder
        base_path = Path(sys._MEIPASS)
    else:
        # Normal execution (project root or script location)
        base_path = Path(__file__).resolve().parent

    return str(base_path / relative_path)


bin_dir = resource_path("binaries")
os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


# Constants and initialize
pygame.init()
WINDOW_SIZE = (700, 860)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("VidGet - Video Downloader")
clock = pygame.time.Clock()
manager = pygame_gui.UIManager(WINDOW_SIZE, resource_path("./stylesheets/glb_theme.json"))

y = 130
gap = 70


# Label constructor
def label(text, y_pos, obj_id: str):
    return UILabel(
        pygame.Rect(20, y_pos, 600, 25),
        text,
        manager=manager,
        container=main,
        object_id=ObjectID(class_id = "@label", object_id=obj_id)
    )

# Set color in batches
def set_color_for_buttons(btns: list[pygame_gui.elements.UIButton], colours_list: list[pygame.Color] = None):
    if not colours_list:
        for button in btns:
            button.colours["normal_bg"] = pygame.Color("#ffffff")
            button.colours["hovered_bg"] = pygame.Color("#ffffff")
            button.colours["disabled_bg"] = pygame.Color("#ffffff")
            button.colours["selected_bg"] = pygame.Color("#b3ffff")
            button.colours["active_bg"] = pygame.Color("#ffffff")
            button.colours["normal_border"] = pygame.Color("#3e3e3e")
            button.colours["normal_text"] = pygame.Color("#000000")
            button.rebuild()
    else:
        colours_list += [None]*5
        for button in btns:
            button.colours["normal_bg"] = colours_list[0]
            button.colours["hovered_bg"] = colours_list[1] or pygame.Color("#ffffff")
            button.colours["disabled_bg"] = colours_list[2] or pygame.Color("#ffffff")
            button.colours["selected_bg"] = colours_list[3] or pygame.Color("#b3ffff")
            button.colours["active_bg"] = colours_list[4] or pygame.Color("#ffffff")
            button.colours["normal_border"] = colours_list[5] or pygame.Color("#3e3e3e")
            button.colours["normal_text"] = colours_list[6] or pygame.Color("#000000")
            button.rebuild()




# The base background
bg = UIPanel(
    relative_rect=pygame.Rect((0, 0), WINDOW_SIZE),
    manager = manager,
    object_id=ObjectID(class_id = "@panel", object_id="#background")
)

# Main panel
main = UIPanel(
    pygame.Rect(30, 40, 640, 780),
    manager=manager,
    object_id=ObjectID(class_id = "@panel", object_id="#main_panel")
)

# Header of main panel
header = UIPanel(
    pygame.Rect(0, 0, 640, 130),
    manager = manager,
    container=main,
    object_id=ObjectID(class_id = "@panel", object_id="#header")
)

# Title of main panel
title = UILabel(
    pygame.Rect(0, 20, 640, 60),
    "VidGet",
    manager=manager,
    container=header,
    object_id=ObjectID(class_id = "@label", object_id="#title")
)

# Subtitle of main panel
subtitle = UILabel(
    pygame.Rect(0, 65, 640, 40),
    "Tải video, âm thanh từ trên YouTube và mạng xã hội miễn phí.",
    manager=manager,
    container=header,
    object_id=ObjectID(class_id = "@label", object_id="#subtitle")
)



# URL
label("Đường liên kết (URL)", y, "#_url")
url_input = UITextEntryLine(
    pygame.Rect(20, y + 30, 600, 40),
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@textentryline", object_id="#url")
)
url_input.set_text("https://youtube.com/watch?v=...")
y += gap

# Format dropdown
label("File đầu ra", y, "#_outfile")
format_dropdown = UIDropDownMenu(
    ["mp4 (video)", "webm (video)", "webp (ảnh)", "png (ảnh)", "mp3 (âm thanh)", "ogg (âm thanh)", "aac (âm thanh)", "wav (âm thanh)"],
    "mp4 (video)",
    pygame.Rect(20, y + 30, 600, 40),
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@dropdownmenu", object_id="#format")
)
# Manual styling
format_dropdown.shape = "rounded_rectangle"
format_dropdown.shape_corner_radius = [4, 4, 4, 4]
format_dropdown.rebuild()
y += gap

# Save path
label("Lưu tới...", y, "#_save")
path_input = UITextEntryLine(
    pygame.Rect(20, y + 30, 600, 40),
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@textentryline", object_id="#save")
)
path_input.set_text(saved_path := fr"C:\Users\{os.getlogin()}\Downloads")
y += gap

# Bitrate
label("Bitrate", y, "#_bitrate")
bitrate_input = UITextEntryLine(
    pygame.Rect(20, y + 30, 600, 40),
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@textentryline", object_id="#bitrate")
)
bitrate_input.set_text(str(bitrate := 192))
y += gap + 10

# File name
label("Tên tệp", y, "#_filename")
filename = UITextEntryLine(
    pygame.Rect(20, y + 30, 600, 40),
    manager = manager,
    container = main,
    placeholder_text="Theo tiêu đề (nếu có)",
    object_id=ObjectID(class_id = "@textentryline", object_id="#filename")
)
y += gap + 10

# Checkbox: do embed metadata
embed_metadata = UICheckBox(
    pygame.Rect(20, y, 30, 30),
    "Gắn các thông tin bổ sung",
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@checkbox", object_id="#metadata")
)
embed_metadata.shape = "rounded_rectangle"
embed_metadata.shape_corner_radius = [4, 4, 4, 4]
embed_metadata.rebuild()
y += 35

# Checkbox: do embed thumbnail
embed_thumbnail = UICheckBox(
    pygame.Rect(20, y, 30, 30),
    "Gắn ảnh nền",
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@checkbox", object_id="#thumbnail")
)
embed_thumbnail.shape = "rounded_rectangle"
embed_thumbnail.shape_corner_radius = [4, 4, 4, 4]
embed_thumbnail.rebuild()


# Button: about
about_button = UIButton(
    pygame.Rect(500, y-35, 110, 30),
    "Về chúng tôi",
    manager = manager,
    container=main,
    tool_tip_text="Xem thêm thông tin về nhà phát triển."
)
# Heavy manual styling
about_button.shape = "rounded_rectangle"
about_button.shape_corner_radius = [4, 4, 4, 4]
about_button.colours.update(
    normal_text = pygame.Color("#ffffff"),
    normal_bg = (abg := pygame_gui.core.ColourGradient(70, pygame.Color("#00c2c2"), pygame.Color("#c200c2"))),
    hovered_bg = abg,
    disabled_bg = abg,
    selected_bg = abg,
    active_bg = abg,
    normal_border = (bd:=pygame.Color("#afafaf")),
    hovered_border = bd,
    disabled_border = bd,
    selected_border = bd,
)
about_button.rebuild()
y += 60
set_color_for_buttons([embed_metadata, embed_thumbnail], [
    x:=pygame.Color("#ffffff"),
    pygame.Color("#ffffff"),
    x,
    pygame.Color("#3fffb2"),
    x,
    z:=pygame.Color("#000000")
])



# Download button
download_btn = UIButton(
    pygame.Rect(20, y, 290, 45),
    "Bắt đầu tải",
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@button", object_id="#download")
)
# Manual styling
download_btn.shape = "rounded_rectangle"
download_btn.shape_corner_radius = [5, 5, 5, 5]
set_color_for_buttons([download_btn], [
    x:=pygame_gui.core.ColourGradient(136, pygame.Color("#667eea"), pygame.Color("#764ba2")),
    x,
    x,
    x,
    x
])

# Cancel button
clear_btn = UIButton(
    pygame.Rect(330, y, 290, 45),
    "Hủy bỏ",
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@button", object_id="#cancel")
)
# Manual styling
clear_btn.shape = "rounded_rectangle"
clear_btn.shape_corner_radius = [5, 5, 5, 5]
set_color_for_buttons([clear_btn], [
    x:=pygame_gui.core.ColourGradient(136, pygame.Color("#ed5d0f"), pygame.Color("#764ba2")),
    x,
    x,
    x,
    x
])
y += 70




# Progress panel
progress_panel = UIPanel(
    pygame.Rect(20, y, 600, 100),
    manager=manager,
    container=main,
    object_id=ObjectID(class_id = "@panel", object_id="#progress"),
    visible=False
)

# Progress label: upper
progress_label = UILabel(
    pygame.Rect(0, 5, 600, 25),
    "Đang tải...",
    manager=manager,
    container=progress_panel,
    object_id=ObjectID(class_id = "@label", object_id="#progress_text")
)

# Progress panel: bar
progress_bar = UIProgressBar(
    pygame.Rect(20, 40, 560, 20),
    manager=manager,
    container=progress_panel,
    object_id=ObjectID(class_id = "@progressbar", object_id="#progress_bar")
)

# Progress label: lower
status_label = UILabel(
    pygame.Rect(0, 65, 600, 25),
    "Đang tải...",
    manager=manager,
    container=progress_panel,
    object_id=ObjectID(class_id = "@label", object_id="#status")
)

# Etc...
progress_value = 0.0
downloading = False
background_color = pygame_gui.core.ColourGradient(136, pygame.Color("#667eea"), pygame.Color("#764ba2"))



# About panel
about_panel = UIPanel(
    pygame.Rect(30, 40, 640, 780),
    manager = manager,
    object_id="#aboutpanel"
)
about_panel.background_colour = pygame.Color("#ffffff")
about_panel.rebuild()

# About panel: header
header2 = UIPanel(
    pygame.Rect(0, 0, 640, 130),
    manager = manager,
    container=about_panel,
    object_id="#header2"
)
# Manual styling
header2.background_colour = background_color
header2.shape = "rounded_rectangle"
header2.shape_corner_radius = [4, 4, 4, 4]
header2.rebuild()

# About panel: title
title2 = UILabel(
    pygame.Rect(0, 20, 640, 60),
    "VidGet",
    manager=manager,
    container=header2,
    object_id="#title2"
)

# About panel: subtitle
subtitle2 = UILabel(
    pygame.Rect(0, 65, 640, 40),
    "Tải video, âm thanh từ trên YouTube và mạng xã hội miễn phí.",
    manager=manager,
    container=header2,
    object_id=ObjectID(class_id = "@label", object_id="#subtitle2")
)


# About panel: back button
back_btn = UIButton(
    pygame.Rect(175, 720, 290, 45),
    "Quay lại",
    manager=manager,
    container=about_panel,
    object_id=ObjectID(class_id = "@button", object_id="#back")
)
# Heavy manual styling
back_btn.shape = "rounded_rectangle"
back_btn.shape_corner_radius = [5, 5, 5, 5]
set_color_for_buttons([back_btn], [
    x:=pygame_gui.core.ColourGradient(136, pygame.Color("#ed0fb5"), pygame.Color("#4b62a2")),
    x,
    x,
    x,
    x
])
back_btn.rebuild()



# Texts in about tab
text_info = """
VidGet - v0.0.1 (pre-alpha)
(Đây là phiên bản thử nghiệm, lỗi có thể xảy ra bất cứ lúc nào)
Được tạo ra bởi: Overseer (Dương Trương Đức Minh)
Có sự giúp đỡ của: Nguyễn Minh Tài, Tập thể lớp 12A1, Cộng Đồng Codebreaker.
Thư viện và phần mềm được sử dụng trực tiếp:
- <a href="https://github.com/pyinstaller/pyinstaller">pyinstaller</a>
- <a href="https://www.ffmpeg.org">ffmpeg</a>
- <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a>
- <a href="https://www.python.org">python</a>
- <a href="https://github.com/pygame-community/pygame-ce">pygame-ce</a>
- <a href="https://github.com/MyreMylar/pygame_gui">pygame-gui</a>
Ghé thăm trang chính của VidGet tại <a href = "https://github.com/OverseerArk/lqd_ytdl-toolchain">đây</a>
"""


# Text box
info = pygame_gui.elements.UITextBox(
    text_info,
    pygame.Rect(30, 160, 580, 520),
    manager = manager,
    container=about_panel,
    object_id="#info"
)
info.background_colour = pygame.Color("#ffffff")
info.parser.current_style["font_color"] = pygame.Color("#000000")
info.rebuild()

def print_error(err_message: str, translated_err_message = ""):
    global c_tab_err
    c_tab_err = True
    console.print(f"[red]Error[/red]: {err_message}")
    translated_err_message = translated_err_message or resolver(err_message)
    info.set_text(
        f"""Lỗi: {translated_err_message}
Chi tiết: {err_message}
""")
    switch_to_about_tab()

def reset_error_message():
    info.set_text(text_info)
    info.rebuild()


# Additional methods
def switch_to_about_tab():
    main.hide()
    download_btn.disable()
    about_panel.show()

def disable_about_tab():
    global c_tab_err
    about_panel.hide()
    download_btn.enable()
    if c_tab_err:
        reset_error_message()
        c_tab_err = False
    main.show()


# Display progress
def progress_hook(d: dict):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        downloaded = d.get('_downloaded_bytes_str', 'N/A')
        total = d.get('_total_bytes_str', 'N/A')
        
        queue.put({"percent": percent, "speed": speed, "eta": eta, "downloaded_b": downloaded, "total_b": total})
    
    elif d['status'] == 'finished':
        queue.put("finished")

def post_processor_hook(d):
    queue.put((x, d['info_dict'].get('filepath', '')) if (x:=d['status']) != 'finished' else False)


# Download
def download(
        url: str,
        codec: str,
        bitrate: int,
        ffmpeg_path: str,
        embed_thumbnail: bool,
        embed_metadata: bool,
        output_dir: str,
        output_template: str = "%(playlist|)s/%(title)s - %(channel)s.%(ext)s"
        ) -> None:

    if downloading:
        print("Can't spawn another thread. ThreadSpawnDenied.")
        return

    video = ["mp4", "webm"]
    image = ["webp", "png"]
    audio = ["mp3", "ogg", "aac", "wav"]
    
    options = {
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ",
                "AppleWebKit/537.36 (KHTML, like Gecko) ",
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
        'progress_hooks': [progress_hook],
        'postprocessor_hooks': [post_processor_hook],
        "outtmpl": os.path.join(output_dir, output_template),
        "writethumbnail": embed_thumbnail or codec in image,
        "postprocessors": [],
        "verbose": True,
        "noplaylist": False,
        "continuedl": True,
        "nopart": False,
        "ffmpeg_location": ffmpeg_path,
        "js_runtimes": {"deno": {"path": resource_path("./deno.exe")}},
        "force_ipv4": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30
    }
    
    if codec in video:
        options["format"] = f"bestvideo[ext={codec}]+bestaudio/best[ext={codec}]/best"
        options["merge_output_format"] = codec
    elif codec in audio:
        options["format"] = "bestaudio/best"
    elif codec in image:
        options["skip_download"] = True
    else:
        options["format"] = "best"
    
    if codec in audio:
        options["postprocessors"].append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
            "preferredquality": str(bitrate)
        })
    
    if embed_thumbnail and (codec in audio or codec in video):
        options["postprocessors"].append({"key": "EmbedThumbnail"})
    
    if embed_metadata:
        options["postprocessors"].append({
            "key": "FFmpegMetadata",
            "add_metadata": True
        })
    
    if codec in image:
        options["postprocessors"].append({
            "key": "FFmpegThumbnailsConvertor",
            "format": codec
        })
    
    with YoutubeDL(options) as dl:
        dl.download([url]) 


def handle_downloading():
    # Lock the downloading button as well as downloading state (no chaos)
    # Get text from textinputs
    # Process it
    # Feed it to "download()"

    if not (text:=url_input.text):
        print("Skipped download because url isn't provided")
        return

    download_btn.disable()
    
    try:
        global download_worker
        download_worker = thread.submit(
            download, 
            url = text, 
            codec = format_dropdown.selected_option[0][:4].strip(), 
            bitrate = bitrate_input.text, 
            ffmpeg_path = resource_path("./binaries/ffmpeg.exe"), 
            embed_thumbnail = embed_thumbnail.is_checked,
            embed_metadata = embed_metadata.is_checked,
            output_dir = path_input.text,
            output_template = filename.text or "%(playlist|)s/%(title)s - %(channel)s.%(ext)s"
            )
        print(f"Spawned a thread. ({thread._threads}) | Thread running state: {download_worker.running() or download_worker.done()}")
        download_worker.add_done_callback(pray)
    except (Exception, SystemExit) as errm:
        print(errm)
    
def resolver(s: str):
    s = str(s).lower()
    if "timeout" in s:
        return "Truy cập https vượt quá thời hạn."
    elif "url" in s:
        return "Đường liên kết (url) lỗi. Hãy kiểm tra lại chính tả và đường liên kết."
    elif "connectionerror" in s:
        return "Lỗi kết nối. Hãy thử lại sau."
    elif "extractor" in s:
        return "Hiện tại chưa có bộ xử lý cho trang web này. Nếu bạn muốn thêm một bộ xử lý, hãy tạo một yêu cầu trên GitHub của VidGet hoặc báo với admin."
    elif ("login" in s) or ("sign" in s) or ("401" in s and "http" in s):
        return "Trang web này yêu cầu đăng nhập để xác minh. Không thể tải dữ liệu từ trang web theo yêu cầu."
    elif ("format" in s) or ("ffmpeg" in s) or ("postprocessing" in s):
        return "Kiểu file đầu ra không thể được xử lý hoặc không phù hợp với nguồn."
    elif ("permission" in s) or ("no space" in s) or ("invalid filename" in s) or ("file exists" in s):
        return "Không thể lưu tệp. Hãy kiểm tra quyền của ứng dụng hoặc bộ nhớ lưu trữ."
    elif ("interrupt" in s) or ("cancelled" in s):
        return "Việc tải xuống bị dừng lại bởi hệ thống."
    elif ("403" in s and "http" in s) or ("too many requests" in s):
        return "Trang web này đang chặn tải xuống. Hãy thử lại sau."
    else:
        return f"Lỗi không xác định: {s}. Bạn nên báo với admin về lỗi này."

def pray(*_):
    """This function is mainly used for debug purpose only.
    
    It will print the data about thread, give error messages as well as stop download UI.
    
    Also, keep praying :)
    """
    global is_completed_download, downloading
    print(f"Worker finished. Object properties: {download_worker.done()=} {download_worker.running()=} {(yt_dlp_exc:=download_worker.exception())}")
    if yt_dlp_exc:
        downloading = False
        print_error(yt_dlp_exc, resolver(yt_dlp_exc))
    is_completed_download = True

def handle_fetch_data() -> dict[str, str]:
    "This function used to fetch the data from queue. Will ignore empty queue error if have."
    try:
        data: dict[str, str] = queue.get_nowait()
        return data
    except:
        ...


# Reset state
def reset_app_state() -> None:
    ...


# Main loop
c_tab_about = False
c_tab_err = False
running = True
postprocessor_map: dict[str, str] = {
    "started": "Đang bắt đầu xử lý",
    "processing": "Đang xử lý",
    "finished": "Đã hoàn tất"
}
is_completed_download: bool = False

def main_app():
    "Main function used to operate the app."
    global running, time_delta, c_tab_about, c_tab_err, thread, downloading, is_completed_download
    while running:
        time_delta = clock.tick(60) / 1000

        set_color_for_buttons(format_dropdown.current_state.active_buttons)

        if c_tab_about:
            switch_to_about_tab()
        else:
            disable_about_tab()
            progress_panel.hide() if not downloading else ...

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == download_btn:
                    is_completed_download = False
                    progress_panel.show()
                    progress_value = 0
                    handle_downloading()
                    downloading = True
                    status_label.set_text("Đang chuẩn bị...")
                    progress_label.set_text(f"Đang tải {url_input.text}")
                    

                elif event.ui_element == clear_btn:
                    progress_panel.hide()
                    progress_value = 0.0
                    thread.shutdown(False)
                    thread = ThreadPoolExecutor(1)
                    status_label.set_text("")
                    progress_bar.set_current_progress(0.0)
                    downloading = False
                
                elif event.ui_element == back_btn:
                    c_tab_about = not c_tab_about
                
                elif event.ui_element == about_button:
                    c_tab_about = not c_tab_about
                
            if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
                webbrowser.open_new_tab(event.link_target)

            manager.process_events(event)
        
        if is_completed_download:
            progress_label.set_text("Đã hoàn tất việc tải xuống và xử lý tệp.")
            status_label.set_text("")
            progress_bar.set_current_progress(100.0)
        elif not downloading:
            progress_label.set_text("")
            status_label.set_text("")
            progress_bar.set_current_progress(0.0)

        if downloading:
            if data:=handle_fetch_data():
                if isinstance(data, tuple):
                    progress_label.set_text("Đang xử lý các thành phần bổ sung...")
                    stage = data[0]
                    status_label.set_text(f"{postprocessor_map[stage]}")
                elif not data:
                    progress_label.set_text(f"Đã hoàn tất. File: {data[1]}")
                    status_label.set_text("")
                    print("Done.")
                    downloading = False
                else:
                    if isinstance(data, dict):
                        progress_value = data.get("percent")
                        speed = data.get("speed")
                        eta = data.get("eta")
                        downloaded_bytes = data.get("downloaded_b")
                        # downloaded_total = data.get("total_b")   - Not used

                        clean = strip_ansi(progress_value).strip()

                    if clean.endswith("%"):
                        try:
                            progress = float(clean.rstrip("%"))
                            progress_bar.set_current_progress(progress)
                        except ValueError:
                            pass

                        stage = ('Đang tải', 1) if data else ('Đang xử lí', 0)
                        if stage[1]:
                            additional = f"{progress_value}, còn khoảng: {eta}, tốc độ: {speed}, đã tải xuống: {downloaded_bytes}"
                        status_label.set_text(f"{stage[0]}{additional}")
                    else:
                        status_label.set_text("Đã tải xuống thành công.")
                

                    if progress >= 100.0:
                        status_label.set_text("Tải xuống thành công!")
                        progress_bar.set_current_progress(100)

        manager.update(time_delta)

        screen.fill((230, 230, 240))
        manager.draw_ui(screen)
        pygame.display.flip()

# main_app()  # Debug only


# Abtract error
try:
    main_app()
except (TypeError, NameError, ValueError, AttributeError, KeyError, IndexError, ImportError) as e:
    os.system(resource_path("./error.exe") + f" 'Error: {e}'")
    console.print(f"[red]Error[/red]: {e}")
    os.system(f"echo {e} && pause")
except Exception as e:
    e = str(e)
    print_error(e, resolver(e))
    main_app()

print("Process exited.")

pygame.quit()