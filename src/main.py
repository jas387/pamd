__version__ = '0.0.1'

# imports

import sys
import json
import flet
import yt_dlp
# constants


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
    def start(self):
        with yt_dlp.YoutubeDL(self.options) as ydl:
            ydl.download(self.url)

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
    def __init__(self,url:str=None):
        self._can_download = False
        self.download = None
        self.url = flet.Ref[flet.TextField]()
        super().__init__(modal=True)
        self.set_title('add download')
        self.set_content(
                    flet.TextField(ref=self.url,label='url', icon=flet.icons.ADD_LINK,autofocus=True),
                    flet.Container(expand=1),
                    flet.Row(alignment=flet.MainAxisAlignment.CENTER,controls=[
                        flet.IconButton(icon=flet.icons.ANALYTICS,tooltip='analyse url',expand=1, on_click=self._analyse)
                        ]))
        self.__url = url
    
    def show(self, page):
        page.dialog = self
        self.open = True
        page.update()
        if self.__url is not None:
            self.url.current.value = self.__url
            self._analyse()
            


    def _analyse(self ,event):
        if len(self.url.current.value)<=0:
            return
        self.set_title('analysing download')
        self.set_content(flet.Text('wait a second while yt-dlp analyse url...'))
        
        self.download = Download(self.url.current.value, logger=self.on_logger)
        #dw.on_logger = self.on_logger
        self.download.analyse()
        self.set_title('download')
        self.download_info = dw_info = DownloadInfo(self.download)
        self.set_content(dw_info)
        self.set_actions(flet.IconButton(icon=flet.icons.DOWNLOAD, on_click=self._start_download))
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

    def set_actions(self, *w):
        self.actions = w
        self.actions_alignment = flet.MainAxisAlignment.CENTER
        self._update()

    def _start_download(self, event):
        self._can_download = True
        self.on_can_start(self)
        self.close(None)

    def on_can_start(self, alert, *w, **kw):
        pass
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
        if not self.page.platform=='android':
            self.page.window_max_width = self.width
            self.page.window_max_height = self.height
            self.page.update()
        # UI
        self.view=flet.ListView(expand=True,auto_scroll=True)
        self.home = Home(view=self.view)
        self.page.floating_action_button = flet.FloatingActionButton(
            icon=flet.icons.ADD, on_click=self._on_click_add_button)
        self.page.add(flet.SafeArea(content=self.home,expand=True))
        
    def _on_click_add_button(self, event, url: str=None):
       dialog = AddDownloadDialog(url=url)
       dialog.on_can_start = self.on_can_start
       dialog.show(self.page)

    def on_can_start(self, alert, *w, **kw):
        info = alert.download
        title = flet.Ref[flet.Text]()
        size = flet.Ref[flet.Text]()
        progress = flet.Ref[flet.ProgressBar]()
        new_dw=flet.Row(controls=[
            flet.Column(controls=[flet.Image(src=info.thumbnail,fit=flet.ImageFit.CONTAIN,width=100,height=100)]),
            flet.Column(controls=[
                flet.Text(f'title: {info.title}',ref=title),
                flet.Text(f'size: {sizeof_fmt(info.filesize_approx)}',ref=size),
                flet.ProgressBar(ref=progress,width=self.page.width/2, value=0)
                ])
            ])
        
        def progress_hooks(entries):
            print('progress_hooks')
            _status = entries['status']
            _info = entries['info_dict']
            if _status == 'downloading':
                _filename = _info['filename']
                _filesize_on_disk = _info['downloaded_bytes']
                _filesize = _info['total_bytes'] or _info['total_bytes_estimate']
                _speed = _info['speed']
                size.current.value = f'{sizeof_fmt(_filesize_on_disk)}/{sizeof_fmt(_filesize)} - {_speed}'
                progress.current.value = _filesize_on_disk /_filesize
                size.current.update()
                progress.current.update()
        
        def on_logger(msg):
            print('on_logger:',msg)

        alert.download.progress_hooks = progress_hooks
        alert.on_logger = on_logger

        self.view.controls.append(flet.SafeArea(content=new_dw,expand=True))
        self.view.update()

        alert.download.start()
        alert.close(None)

# refactoring code, the old one its too dirty :(
import re
import flet
import concurrent.futures
class App:
    def __init__(self, width: int=None, height: int=None):
        self.page = None
        self.view = flet.Ref[flet.ListView|flet.GridView]()
        self.add_download_button = flet.Ref[flet.FloatingActionButton]()
    
    def main(self, page: flet.Page):
        self.page = page
        self.page.on_keyboard_event = self._on_keyboard
        self.view=flet.ListView(ref=self.view,controls=[

            ])
        page.floating_action_button = flet.FloatingActionButton(ref=self.add_download_button, icon=flet.icons.ADD,on_click=self._show_add_download_dialog)
        page.add(flet.SafeArea(content=self.view,expand=True))
        



    def _show_add_download_dialog(self, e, url:str=None):
        download = Download(self.page, self.view,url=url)
        return url

    def _on_keyboard(self, e):
        ctrl = e.ctrl
        key = e.key
        if ctrl:
            match (key):
                case 'N':
                    self._show_add_download_dialog(None)

class Download:
    def __init__(self, page: flet.Page,view,url:str=None):
        self.__info = {}
        self.page = page
        self.view = view
        self._show_analyse_dialog(url=url)
    def _show_analyse_dialog(self,url: str=None):
        def on_change_url(e):
            value = e.data
            print(value)
            if len(value)<=0:
                e.control.error_hint = 'invalid url!'
                analyse_button.disabled = True
            else:
                analyse_button.disabled=False
            analyse_button.update()
            e.control.update()
        def on_submit_url(e):
            #print(dir(yt_dlp))
            text_field.current.disabled = True
            analyse_button.disabled = True
            text_field.current.update()
            analyse_button.update()
            is_valid_url = False
            for extractor in yt_dlp.list_extractors():
                description = extractor.IE_DESC
                name = extractor.IE_NAME
                valid_url = extractor._VALID_URL
                if valid_url is False:
                    continue
                if re.match(valid_url,text_field.current.value) != None:
                    is_valid_url = True
                    break
            if not is_valid_url:
                text_field.current.error_hint = 'no extractor found for this url!'
                text_field.current.update()
            else:
                dialog.open = False
                dummy=url is not None
                self._show_analysing_dialog(text_field.current.value, dummy=dummy)
            self.page.update()

        url_filter = flet.InputFilter(r"^\w{1,5}://.*")
        text_field = flet.Ref[flet.TextField]()
        analyse_button = flet.IconButton(icon=flet.icons.ANALYTICS,disabled=True,on_click=on_submit_url)
        dialog = flet.AlertDialog(modal=False,title=flet.Text('analyse download'),
            content=flet.TextField(ref=text_field,hint_text='url',keyboard_type=flet.KeyboardType.URL,input_filter=url_filter,icon=flet.icons.LINK, autofocus=True, on_change=on_change_url, on_submit=on_submit_url),
                actions=[
                analyse_button,
                ], actions_alignment=flet.MainAxisAlignment.CENTER)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        if url is not None:
            text_field.current.value = url
            text_field.current.update()
            on_submit_url(None)
            self.page.update()

    def _show_analysing_dialog(self, url: str,dummy:bool=False):
        # https://www.youtube.com/watch?v=nTtdEYRh8WI
        class Logger:
            def debug(self, msg: str):
                if msg.startswith('[debug] '):
                    pass
                else:
                    self.info(msg)
            def info(self, msg: str):
                content_text.current.value = msg
                content_text.current.update()

            def warning(self, msg: str):
                pass

            def error(self, msg: str):
                pass
        def analysing_hook(entries):
            status=entries['status']
            info = entries['info_dict']
            if status == 'finished':
                print('finished')
            elif status =='download':
                print('downloading')
            elif status == 'error':
                print('error')
            dialog.update()


        def start_info_extraction():
            options = dict({'logger':Logger(),'progress_hooks':[analysing_hook]})
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url,download=False)
                self.__info = info
                title = info['title']
                img = info['thumbnail'] or info['thumbnails'][0]
                #size = info['total_bytes'] or info['total_bytes_estimate']
                dialog.content = flet.Column(height=self.page.height/3,alignment=flet.MainAxisAlignment.START, horizontal_alignment=flet.CrossAxisAlignment.CENTER,controls=[
                    flet.Image(src=img,fit=flet.ImageFit.COVER,width=200,height=200,border_radius=flet.border_radius.all(30),),
                    flet.Text(title)
                    ])
                download_button.current.disabled = False
                download_button.current.update()
                if dummy:
                    start_download(None)

        class LoggerDownload:
            def debug(self, msg: str):
                if msg.startswith('[debug] '):
                    pass
                else:
                    self.info(msg)
            
            def info(self, msg: str):
                #print(msg)
                pass

            def warning(self, msg: str):
                pass

            def error(self, msg: str):
                pass
        
        def download_hook(d):
            status = d['status']
            if status == 'downloading':
                downloaded = d['_downloaded_bytes_str']
                total = d['_total_bytes_str']
                if total.endswith('N/A'):
                    total=d['_total_bytes_estimate_str']
                speed = d['_speed_str']

                elapsed_time = d['_elapsed_str']
                estimated_time = d['_eta_str']
                percent = d['_percent_str']
                # UI ajusts
                '''
                downloaded_ref.current.value = downloaded
                total_ref.current.value = total
                speed_ref.current.value = speed
                elapsed_time_ref.current.value = elapsed_time
                estimated_time_ref.current.value = estimated_time
                '''
                all_ref.current.value = f'{downloaded}/{total}/{percent} - {speed} - {elapsed_time}/{estimated_time}'
                progress_ref.current.value = float(percent[:-1])/100
                all_ref.current.update()
                progress_ref.current.update()
                self.page.update()


        def start_download(e):
            info = self.__info
            title = info['title']
            img = info['thumbnail'] or info['thumbnails'][0]
            self.page.close_dialog()
            self.page.update()
            row = flet.Row([flet.Image(src=img,width=200,height=200, fit=flet.ImageFit.CONTAIN),
                flet.Column(height=100,expand=False,controls=[flet.Text(title),
                    flet.Text(ref=all_ref),
                    #flet.Row([
                        #flet.Text(ref=downloaded_ref),flet.Text(ref=total_ref),
                        #flet.Text(ref=speed_ref),flet.Text(ref=elapsed_time_ref),flet.Text(ref=estimated_time_ref),
                    #    ])
                    flet.ProgressBar(ref=progress_ref,width=self.page.width/3)])])
            self.view.controls.append(row)
            self.view.update()
            def download_thread():
                options = {'logger':LoggerDownload(),'progress_hooks':[download_hook]}
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download(url)
            download_thread()

                
        progress_ref = flet.Ref[flet.ProgressBar]()
        downloaded_ref = flet.Ref[flet.Text]()
        total_ref = flet.Ref[flet.Text]()
        speed_ref = flet.Ref[flet.Text]()
        elapsed_time_ref = flet.Ref[flet.Text]()
        estimated_time_ref = flet.Ref[flet.Text]()
        all_ref = flet.Ref[flet.Text]()


        title_text = flet.Ref[flet.Text]()
        download_button = flet.Ref[flet.IconButton]()
        content_text = flet.Ref[flet.Text]()
        dialog = flet.AlertDialog(modal=False,title=flet.Text(ref=title_text,value='analysing url...', text_align=flet.TextAlign.CENTER),
            content=flet.Text(ref=content_text, value='wait a second...'),
                actions=[
                    flet.IconButton(ref=download_button, icon=flet.icons.DOWNLOAD, disabled=True, on_click=start_download)
                ], actions_alignment=flet.MainAxisAlignment.CENTER)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        start_info_extraction()

if __name__ == '__main__':
    app = App(480,640)
    flet.app(app.main)