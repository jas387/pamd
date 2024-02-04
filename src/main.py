__version__ = '0.0.1'

# imports

import sys
import json
import flet
import yt_dlp
# constants
ANDROID_ENVIROMENT_VARS = ('ANDROID_ROOT','ANDROID_ART_ROOT','ANDROID_ASSETS','BOOTCLASSPATH','ANDROID_TZDATA_ROOT','ANDROID_DATA')
IS_ANDROID = any([hasattr(sys,i) for i in ANDROID_ENVIROMENT_VARS])

# functions

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


# class

class DownloadLogger:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass


class Download:
    def __init__(self, url: str, options: dict={},logger: callable=None):
        self.url = url
        self.logger = DownloadLogger()
        self.logger.debug = logger or self.on_logger
        self.logger.info = logger or self.on_logger
        self.logger.warning = logger or self.on_logger
        self.logger.error = logger or self.on_logger
        self.logger_msg = None
        self.options = {'logger':self.logger,'progress_hooks':[self.progress_hooks]} #options
        # analysed vars
        self._id = None
        self.title = None
        self.thumbnail = None
        # internal
        self.info = None
    
    def analyse(self):
        with yt_dlp.YoutubeDL(self.options) as ydl:
            info = ydl.extract_info(self.url, download=False)
            #info = json.dumps(ydl.sanitize_info(info))
            self._id = info['id']
            self.title=info['title']
            self.thumbnail = info['thumbnail'] or info['thumbnails'][0]
            self.filesize_approx = info['filesize_approx']
            self.info = info
            #print(info)
            #print(self.thumbnail)
            #print(self.title)


    def progress_hooks(self, entries):
        status = entries['status']
        info = entries['info_dict']
    def on_logger(self, msg):
        self.logger_msg = msg

class DownloadInfo(flet.UserControl):
    def __init__(self,download: Download):
        super().__init__()
        self.download = download
        # internal
        self.title = flet.Ref[flet.TextField]()
        self.thumbnail = flet.Ref[flet.Image]()
        self.size = flet.Ref[flet.TextField]()
    def build(self):
        return flet.Column(horizontal_alignment=flet.MainAxisAlignment.CENTER,controls=[
            flet.Image(ref=self.thumbnail,src=self.download.thumbnail,fit=flet.ImageFit.CONTAIN),
            flet.Text(ref=self.title,value=f'title: {self.download.title}',text_align=flet.TextAlign.CENTER),
            flet.Text(ref=self.size,value=f'filesize: {sizeof_fmt(self.download.filesize_approx)}',text_align=flet.TextAlign.CENTER)
            ])


class Home(flet.UserControl):
    def __init__(self, view: flet.UserControl=None):
        super().__init__()
        self.view = view

    def build(self):
        window = flet.Column([
            self.view
            ])
        return window

class AddDownloadDialog(flet.AlertDialog):
    def __init__(self):
        self.url = flet.Ref[flet.TextField]()
        super().__init__(modal=True)
        self.set_title('add download')
        self.set_content(
                    flet.TextField(ref=self.url,label='url', icon=flet.icons.ADD_LINK,autofocus=True),
                    flet.Container(expand=1),
                    flet.Row(alignment=flet.MainAxisAlignment.CENTER,controls=[
                        flet.IconButton(icon=flet.icons.ANALYTICS,tooltip='analyse url',expand=1, on_click=self._analyse)
                        ]))

    
    def show(self, page):
        page.dialog = self
        self.open = True
        page.update()

    def _analyse(self ,event):
        self.set_title('analysing download')
        self.set_content(flet.Text('wait a second while yt-dlp analyse url...'))
        # test
        self.url.current.value = 'https://www.youtube.com/watch?v=nTtdEYRh8WI'

        dw = Download(self.url.current.value, logger=self.on_logger)
        #dw.on_logger = self.on_logger
        dw.analyse()
        self.set_title('download')
        dw_info = DownloadInfo(dw)
        self.set_content(dw_info)
        self._update()

    def on_logger(self, msg):
        self.set_content(flet.Text(msg))

    def close(self, event):
        self.open = False
        self._update()

    def set_title(self, text: str):
        self.title = flet.Row(alignment=flet.MainAxisAlignment.CENTER,controls=[
                flet.Text(text,text_align=flet.TextAlign.CENTER,expand=0),
                flet.IconButton(icon=flet.icons.CANCEL, tooltip='cancel',expand=0, on_click=self.close)
            ])

        self._update()
    
    def set_content(self, *w, **kw):
        self.content=flet.Column(horizontal_alignment=flet.MainAxisAlignment.CENTER,controls=w)
        self._update()

    def _update(self):
        try:
            self.update()
            self.page.update()
        except AssertionError:
            pass

class App:
    def __init__(self, width: int=None,height: int=None):
        self.page = None
        self.title = 'PAMD'
        self.width = width
        self.height = height

    def main(self, page: flet.Page):
        self.page = page
        self.page.title = self.title
        if not IS_ANDROID:
            self.page.window_max_width = self.width
            self.page.window_max_height = self.height
            self.page.update()
        # UI
        self.view=flet.ListView(expand=1)
        self.home = Home(view=self.view)
        self.page.floating_action_button = flet.FloatingActionButton(
            icon=flet.icons.ADD, on_click=self._on_click_add_button)
        self.page.add(self.home)

    def _on_click_add_button(self, event):
       dialog = AddDownloadDialog()
       dialog.show(self.page)
if __name__ == '__main__':
    app = App(480,640)
    flet.app(app.main)