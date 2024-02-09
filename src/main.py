__version__ = '0.0.1'

# imports
import re
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



class Storage:
    __PAGE: flet.Page = None
    __NAME = 'com.pamd'
    
    @classmethod
    def set_page(cls, page: flet.Page):
        cls.__PAGE = page

    @classmethod
    def _check_page(cls):
        if cls.__PAGE is None:
            raise ValueError('Storage.set __PAGE is None!')

    @classmethod
    def set(cls, key:str, value: object):
        cls._check_page()
        return cls.__PAGE.client_storage.set(f'{cls.__NAME}.{key}',value)

    @classmethod
    def get(cls, key: str):
        cls._check_page()
        return cls.__PAGE.client_storage.get(f'{cls.__NAME}.{key}')

    @classmethod
    def contains_key(cls, key: str):
        cls._check_page()
        return cls.__PAGE.client_storage.contains_key(f'{cls.__NAME}.{key}')

    @classmethod
    def get_keys(cls, prefix: str):
        cls._check_page()
        return cls.__PAGE.client_storage.get_keys(f'{cls.__NAME}.{prefix}')

    @classmethod
    def remove(cls, key: str):
        cls._check_page()
        return cls.__PAGE.client_storage.remove(f'{cls.__NAME}.{key}')

    
    @classmethod
    def keys(cls):
        cls._check_page()
        return cls.__PAGE.client_storage.get_keys(f'{cls.__NAME}.')

    @classmethod
    def values(cls):
        cls._check_page()
        return [cls.__PAGE.client_storage.get(key) for key in cls.keys()]

    @classmethod
    def clear(cls):
        cls._check_page()
        keys = cls.keys()
        for key in keys:
            cls.__PAGE.client_storage.remove(key)




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
        clipboard = self.page.get_clipboard()
        if re.match(url_filter.regex_string,clipboard) is not None:
            text_field.current.value = clipboard
            text_field.current.update()
            analyse_button.disabled = False
            analyse_button.update()
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

        def format_selector_func(ctx):
            """ Select the best video and the best audio that won't result in an mkv.
            NOTE: This is just an example and does not handle all cases """

            # formats are already sorted worst to best
            formats = ctx.get('formats')[::-1]

            # acodec='none' means there is no audio
            best_video = next(f for f in formats
                              if f['vcodec'] != 'none' and f['acodec'] == 'none')

            # find compatible audio extension
            audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
            # vcodec='none' means there is no video
            best_audio = next(f for f in formats if (
                f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext))

            # These are the minimum required fields for a merged format
            yield {
                'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
                'ext': best_video['ext'],
                'requested_formats': [best_video, best_audio],
                # Must be + separated list of protocols
                'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}'
            }

        def start_info_extraction():
            options = dict({'logger':Logger(),'progress_hooks':[analysing_hook]})  # ,'format':format_selector_func})
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url,download=False)
                self.__info = info
                '''
                for i in info['formats']:
                    resolution = i['resolution']
                    ext = i['ext']
                    video_ext = i['video_ext']
                    audio_ext = i['audio_ext']
                    _format = i['format']
                    _format_id = i['format_id']
                    print(_format)
                '''
                video_options = []
                audio_options = []
                x=True
                class Format:
                    def __init__(self,_dict: dict):
                        self.id = _dict.get('format_id',None)
                        self.ext = _dict.get('ext',None)
                        self.fps = _dict.get('fps',None)
                        self.width = _dict.get('width',None)
                        self.height = _dict.get('height',None)
                        self.vcodec = _dict.get('vcodec',None)
                        self.acodec = _dict.get('acodec',None)
                        self.resolution = _dict.get('resolution',None)
                        self.format = _dict.get('format',None)
                        self.note = _dict.get('format_note',None)
                    
                    def info(self):
                        print('id:',self.id)
                        print('ext:',self.ext)
                        print('fps:',self.fps)
                        print('width:',self.width)
                        print('height:',self.height)
                        print('vcodec:',self.vcodec)
                        print('acodec:',self.acodec)
                        print('resolution:',self.resolution)
                        print('format:',self.format)
                        print('note:',self.note)

                
                for i in info['formats']:
                    if i['video_ext']!='none':
                        video_options.append(Format(i))
                    else:
                        audio_options.append(Format(i))
                title = info['title']
                img = info['thumbnail'] or info['thumbnails'][0]
                #size = info['total_bytes'] or info['total_bytes_estimate']
                def index_format(_formats: list, value: str):
                    for klass in _formats:
                        if klass.format==value:
                            return klass
                    return None
                
                def on_change_video(e):
                    video = dropdown_video_ref.current
                    audio = dropdown_audio_ref.current
                    klass = index_format(video_options,video.value)
                    if klass.acodec!='none':
                        audio.value = ''
                        audio.update()
                
                def on_change_audio(e):
                    video = dropdown_video_ref.current
                    audio = dropdown_audio_ref.current
                    klass = index_format(audio_options,audio.value)
                    if klass.vcodec!='none':
                        video.value = ''
                        video.update()


                dialog.content = flet.Column(alignment=flet.MainAxisAlignment.START, horizontal_alignment=flet.CrossAxisAlignment.CENTER,controls=[
                    flet.Image(src=img,fit=flet.ImageFit.COVER,width=200,height=200,border_radius=flet.border_radius.all(30),),
                    flet.Text(title),
                        flet.Dropdown(ref=dropdown_video_ref,on_change=on_change_video,label='video',value='137 - 1920x1080 (1080p)',options=[flet.dropdown.Option(option.format) for option in video_options]),
                        flet.Dropdown(ref=dropdown_audio_ref,on_change=on_change_audio,label='audio',value='140 - audio only (medium)',options=[flet.dropdown.Option(option.format) for option in audio_options]),
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
            if status == 'finished':
                progress_ref.current.bgcolor = 'green'
                progress_ref.current.value = 1.0
                progress_ref.current.update()
                self.page.update()
            elif status == 'downloading':
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
                flet.Column(height=100,expand=True,controls=[flet.Text(title,expand=True),
                    flet.Text(ref=all_ref),
                    #flet.Row([
                        #flet.Text(ref=downloaded_ref),flet.Text(ref=total_ref),
                        #flet.Text(ref=speed_ref),flet.Text(ref=elapsed_time_ref),flet.Text(ref=estimated_time_ref),
                    #    ])
                    flet.ProgressBar(ref=progress_ref,width=self.page.width/3)])])
            self.view.controls.append(flet.SafeArea(row,expand=True))
            self.view.update()
            audio_format = dropdown_audio_ref.current.value.split(' ')[0]
            video_format = dropdown_video_ref.current.value.split(' ')[0]
            _format_selector = f'{video_format}+{audio_format}'
            template = Storage.get('output_folder')+r'/%(title)s.%(id)s.%(ext)s'
            options = {'logger':LoggerDownload(),'progress_hooks':[download_hook],'outtmpl':template,
            'format':_format_selector}
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download(url)
                
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
        dropdown_audio_ref = flet.Ref[flet.Dropdown]()
        dropdown_video_ref = flet.Ref[flet.Dropdown]()
        dialog = flet.AlertDialog(modal=False,title=flet.Text(ref=title_text,value='analysing url...', text_align=flet.TextAlign.CENTER),
            content=flet.Text(ref=content_text, value='wait a second...'),
                actions=[
                    flet.IconButton(ref=download_button, icon=flet.icons.DOWNLOAD, disabled=True, on_click=start_download)
                ], actions_alignment=flet.MainAxisAlignment.CENTER)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        start_info_extraction()




class DownloadInfo(flet.UserControl):
    def __init__(self,download: Download):
        super().__init__()
        self.download = download
        # internal
        self.title = flet.Ref[flet.TextField]()
        self.thumbnail = flet.Ref[flet.Image]()
        self.size = flet.Ref[flet.TextField]()
    def build(self):
        return flet.SafeArea(content=flet.Column(horizontal_alignment=flet.MainAxisAlignment.CENTER,controls=[
            flet.Image(expand=True,ref=self.thumbnail,src=self.download.thumbnail,fit=flet.ImageFit.CONTAIN),
            flet.Text(expand=True,ref=self.title,value=f'title: {self.download.title}',text_align=flet.TextAlign.CENTER),
            flet.Text(expand=True,ref=self.size,value=f'filesize: {sizeof_fmt(self.download.filesize_approx)}',text_align=flet.TextAlign.CENTER)
            ]))

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
    def __init__(self, width: int=None, height: int=None):
        self.page = None
        self.view = flet.Ref[flet.ListView|flet.GridView]()
        self.add_download_button = flet.Ref[flet.FloatingActionButton]()
        self._width = width
        self._height = height

    
    def main(self, page: flet.Page):
        self.page = page
        Storage.set_page(page)
        if self.page.platform!='android':
            self.page.window_max_width = self._width
            self.page.window_max_height = self._height
        self.page.on_keyboard_event = self._on_keyboard
        self.view=flet.ListView(ref=self.view,controls=[

            ])
        page.floating_action_button = flet.FloatingActionButton(ref=self.add_download_button, icon=flet.icons.ADD,on_click=self._show_add_download_dialog)
        page.add(flet.SafeArea(content=self.view,expand=True))
        # ask for save folder
        self._has_folder = True if Storage.contains_key('output_folder') and Storage.get('output_folder') is not None else False
        color = 'red' if not self._has_folder else 'green'

        self.folder_bt = flet.IconButton(icon=flet.icons.FOLDER_OPEN,icon_color=color,on_click=self._select_folder)
        self.folder_tooltip = flet.Tooltip(message=Storage.get('output_folder'),content=self.folder_bt)
        
        appbar=flet.AppBar(actions=[self.folder_tooltip])
        
        page.add(appbar)
        if not self._has_folder:
            self._select_folder(None)
    
    def _on_focus_folder(self, e):
        print('focus')

    def _select_folder(self, e):
        def on_result(e: flet.FilePickerResultEvent):
            if e.path:
                Storage.set('output_folder', e.path)
                self.folder_tooltip.message = e.path
                self.folder_tooltip.update()
                self.folder_bt.icon_color = 'green'
                self.folder_bt.update()
                self._has_folder = True

        picker = flet.FilePicker(on_result=on_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.get_directory_path(dialog_title='select output folder')

    def _show_add_download_dialog(self, e, url:str=None):
        if self._has_folder:
            download = Download(self.page, self.view,url=url)
            return url
        else:
            self._select_folder(None)

    def _on_keyboard(self, e):
        ctrl = e.ctrl
        key = e.key
        if ctrl:
            match (key):
                case 'N':
                    self._show_add_download_dialog(None)


if __name__ == '__main__':
    app = App(480,640)
    flet.app(app.main)