#! /usr/bin/python
# -*- coding: utf-8 -*-

# tkinter example for VLC Python bindings
# This is an extension of an app created by Patrick Fay in 23-09-2015

import os
import time
import vlc
import pathlib
import platform
import customtkinter as Ctk
from customtkinter import filedialog
from tkinter import messagebox
from threading import Thread, Event

Ctk.set_appearance_mode("System")

class ttkTimer(Thread):
    def __init__(self, callback, tick) -> None:
        super().__init__()
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters


class Player(Ctk.CTkFrame):

    def __init__(self, master, title=None, **kwargs):
        super().__init__(master, **kwargs)

        self.parent = master

        if title == None:
            title = "Video Player"
        self.parent.title(title)

        # Bar
        Frame1 = Ctk.CTkFrame(self.parent)
        Frame1.pack(fill=Ctk.BOTH)

        menubar = Ctk.CTkOptionMenu(
            Frame1, values=["Open File", "Exit"], command=self.select_media_file)
        menubar.pack(side=Ctk.LEFT)
        appearance_mode_optionemenu = Ctk.CTkOptionMenu(
            Frame1, values=["Light", "Dark", "System"], command=self.change_appearance_mode)
        appearance_mode_optionemenu.pack(side=Ctk.RIGHT)
        appearance_mode_optionemenu.set("System")

        # Player
        self.videopanel = Ctk.CTkFrame(self.parent)
        self.canvas = Ctk.CTkCanvas(
            self.videopanel, bg="black")
        self.canvas.pack(fill=Ctk.BOTH, expand=1)
        self.videopanel.pack(fill=Ctk.BOTH, expand=1)

        # contols
        ctrlpanel = Ctk.CTkFrame(self.parent)
        pause = Ctk.CTkButton(ctrlpanel, text="Pause", command=self.OnPause)
        play = Ctk.CTkButton(ctrlpanel, text="Play", command=self.OnPlay)
        stop = Ctk.CTkButton(ctrlpanel, text="Stop", command=self.OnStop)
        volume = Ctk.CTkButton(ctrlpanel, text="Volume",
                               command=self.OnSetVolume)
        pause.pack(side=Ctk.LEFT)
        pause.pack(side=Ctk.LEFT)
        play.pack(side=Ctk.LEFT)
        stop.pack(side=Ctk.LEFT)
        volume.pack(side=Ctk.LEFT)
        self.volume_var = Ctk.IntVar()
        self.volslider = Ctk.CTkSlider(
            ctrlpanel, variable=self.volume_var, command=self.volume_sel, from_=0, to=100)
        self.volslider.pack(side=Ctk.LEFT)
        ctrlpanel.pack(side=Ctk.BOTTOM)

        ctrlpanel2 = Ctk.CTkFrame(self.parent)
        self.scale_var = Ctk.DoubleVar()
        self.timeslider_last_val = ""
        self.timeslider = Ctk.CTkSlider(ctrlpanel2, variable=self.scale_var, command=self.scale_sel,
                                        from_=0, to=1000, height=20)
        self.timeslider.pack(side=Ctk.BOTTOM, fill=Ctk.X, expand=1)
        self.timeslider_last_update = time.time()
        ctrlpanel2.pack(side=Ctk.BOTTOM, fill=Ctk.X)
        
        # Vlc player controls
        self.Instance = vlc.Instance("--no-xlib", "--vout", "x11")
        self.player = self.Instance.media_player_new()

        self.player.video_set_deinterlace(self.str_to_bytes('yadif'))
        self.player.set_fullscreen(True)

        self.timer = ttkTimer(self.OnTimer, 1.0)
        self.timer.start()
        self.parent.update()

    def str_to_bytes(self, input_string):
        if isinstance(input_string, str):
            return input_string.encode('utf-8')
        else:
            raise TypeError("Input must be a string")

    def change_appearance_mode(self, new_appearance):
        Ctk.set_appearance_mode(new_appearance)

    def select_media_file(self, choice):
        if choice == "Exit":
            _quit()

        elif choice == "Open File":
            self.OnOpen()

    def OnExit(self, evt):
        self.Close()

    def SetTitle(self, title: str):
        self.parent.title = title

    def OnOpen(self):
        self.OnStop()

        p = pathlib.Path(os.path.expanduser("~"))
        filetypes = (
            ("video files", "*.mp4 *.mkv *.avi *.mp3"),
            ("all files", "*.*")
        )
        fullname = filedialog.askopenfilename(
            initialdir=p, title="choose your file", filetypes=filetypes)
        if os.path.isfile(fullname):
            dirname = os.path.dirname(fullname)
            filename = os.path.basename(fullname)
            self.Media = self.Instance.media_new(
                str(os.path.join(dirname, filename))
            )
            self.player.set_media(self.Media)

            title = self.player.get_title()
            if title == -1:
                title = filename
            self.SetTitle(title)

            if platform.system() == "Windows":
                self.player.set_hwnd(self.GetHandle())
            else:
                self.player.set_xwindow(self.GetHandle())
            # FIXME:
            self.OnPlay()
            self.volslider.set(self.player.audio_get_volume())

    def OnPlay(self):
        if not self.player.get_media():
            self.OnOpen()
        else:
            if self.player.play() == -1:
                self.errorDialog("Unable to play.")

    def GetHandle(self):
        return self.videopanel.winfo_id()

    def OnPause(self):
        self.player.pause()

    def OnStop(self):
        self.player.stop()
        # reset the time slider
        self.timeslider.set(0)

    def OnTimer(self):
        if self.player == None:
            return

        length = self.player.get_length()
        dbl = length * 0.001
        self.timeslider.configure(to=dbl)

        tyme = self.player.get_time()
        if tyme == -1:
            tyme = 0
        dbl = tyme * 0.001
        self.timeslider_last_val = ("%.0f" % dbl) + ".0"
        if time.time() > (self.timeslider_last_update + 2.0):
            self.timeslider.set(dbl)

    def scale_sel(self, evt):
        if self.player == None:
            return
        nval = self.scale_var.get()
        sval = str(nval)
        if self.timeslider_last_val != sval:
            self.timeslider_last_update = time.time()
            mval = "%.0f" % (nval * 1000)
            self.player.set_time(int(mval))  # expects milliseconds

    def volume_sel(self, evt):
        if self.player == None:
            return
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def OnToggleVolume(self, evt):
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        self.volume_var.set(self.player.audio_get_volume())

    def OnSetVolume(self):
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            try:
                self.errorDialog("Failed to set volume")
            except TypeError:
                self.errorDialog("Wrong Type")

    def errorDialog(self, errormessage):
        edialog = messagebox.showerror(title="Error", message=errormessage)
        return edialog

    def OnExit(self):
        self.Close()


def Tk_get_root():
    if not hasattr(Tk_get_root, "root"):
        Tk_get_root.root = Ctk.CTk()
    return Tk_get_root.root


def _quit():
    print("_quite: see you soon guffer!")
    root = Tk_get_root()
    root.quit()
    root.destroy()
    os._exit(1)


if __name__ == '__main__':
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)
    root.geometry("700x500")
    player = Player(root, title="Video Player")
    root.mainloop()
