import codecs
import glob
import os
import tkinter
import webbrowser
from tkinter import Tk, Label, Button, filedialog, StringVar, Frame

import requests
from PIL import ImageTk, Image, UnidentifiedImageError


class MarkupProcess:
    def __init__(self, markup_folder: str):
        self.markup_folder = markup_folder

        if not os.path.exists(self.markup_folder):
            raise ValueError(f"{self.markup_folder} does not exist")
        if not os.path.isdir(self.markup_folder):
            raise ValueError(f"{self.markup_folder} does not folder")

        self.need_markup, self.marked = list(), list()
        self.fill_lists()

    def fill_lists(self):
        folders_lst = list(filter(
            os.path.isdir,
            map(lambda d: os.path.join(self.markup_folder, d), os.listdir(self.markup_folder))
        ))
        self.need_markup, self.marked = list(), list()

        try:
            for folder in folders_lst:
                check_folder = os.path.join(self.markup_folder, folder)
                if self.is_marked(glob.glob(os.path.join(check_folder, '*.txt'))[0]):
                    self.marked.append(check_folder)
                else:
                    self.need_markup.append(check_folder)
        except IndexError:
            print(f"Can't parse folder: {self.markup_folder}")

    def get_current(self) -> dict:
        element = dict()
        if self.need_markup_count > 0:
            cur_folder = self.need_markup[0]
            element["folder_path"] = cur_folder
            try:
                element["img_path"] = glob.glob(os.path.join(cur_folder, "*.jpg"))[0]
            except IndexError:
                element["img_path"] = None
            element["txt_path"] = glob.glob(os.path.join(cur_folder, "*.txt"))[0]
            with codecs.open(element["txt_path"], "r", "utf-8") as f_txt:
                items = f_txt.read().strip().split()
                element["req_id"] = items[0]
                element["key_words"] = items[1:-1]
                element["url"] = items[-1]

        return element

    def set_marked(self, folder_path: str):
        if folder_path in self.need_markup:
            self.need_markup.remove(folder_path)
            self.marked.append(folder_path)

    @staticmethod
    def is_marked(path_txt: str) -> bool:
        if not os.path.exists(path_txt):
            raise ValueError(f"{path_txt} does not exist")
        if not os.path.isfile(path_txt):
            raise ValueError(f"{path_txt} does not file")
        with open(path_txt, "r") as f_txt:
            elements = f_txt.read().strip().split()

        try:
            last_el = int(elements[-1])
            return last_el in (-1, 1)
        except ValueError:
            return False

    @property
    def need_markup_count(self):
        return len(self.need_markup)

    @property
    def marked_count(self):
        return len(self.marked)

    @property
    def total_count(self):
        return self.need_markup_count + self.marked_count


class MyFirstGUI:
    def __init__(self, master):
        self.master = master
        master.title("Marking")

        self.canvas = Label(master)
        self.canvas.pack(fill=tkinter.BOTH, expand=1)

        self.next_frame = Frame(master)
        self.next_frame.pack()

        self.pass_button = Button(self.next_frame, text="1",
                                  command=lambda: self.set_answer(1), state=tkinter.DISABLED)
        self.deny_button = Button(self.next_frame, text="-1",
                                  command=lambda: self.set_answer(-1), state=tkinter.DISABLED)

        self.pass_button.pack(side=tkinter.RIGHT)
        self.deny_button.pack(side=tkinter.LEFT)

        self.key_words = StringVar(master)
        self.key_words_label = Label(master, textvariable=self.key_words)
        self.url = StringVar(master)
        self.url_label = Label(master, textvariable=self.url)
        self.key_words_label.pack()
        self.url_label.pack()

        self.settings_frame = Frame(master)
        self.settings_frame.pack()

        self.select_folder = Button(self.settings_frame, text="Dir", command=self.select_markup_folder)
        self.close_button = Button(self.settings_frame, text="Close", command=master.quit)
        self.select_folder.pack(side=tkinter.LEFT)
        self.close_button.pack(side=tkinter.RIGHT)

        self.markup_folder = os.path.dirname(os.path.realpath(__file__))
        self.markup_processor = None

        self.current_element = dict()

        self.status_bar_string = StringVar(master, "Marked: 0 | Need: 0 | Total: 0")
        self.status_bar = Label(master, textvariable=self.status_bar_string,
                                bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W)
        self.status_bar.pack(side=tkinter.BOTTOM, fill=tkinter.X)

        self.master.bind("<Key>", self.key_callback)

    def key_callback(self, event):
        if event.keycode == 37:
            self.set_answer(-1)
        elif event.keycode == 39:
            self.set_answer(1)
        elif event.keycode == 40:
            self.master.clipboard_clear()
            self.master.clipboard_append(self.current_element.get("url"))
        elif event.keycode == 38:
            webbrowser.open(self.current_element.get("url"))

    def select_markup_folder(self):
        self.markup_folder = filedialog.askdirectory(initialdir=self.markup_folder, title="Select markup folder")
        print(f"{self.markup_folder} was selected")
        try:
            self.markup_processor = MarkupProcess(self.markup_folder)
            self.current_element = self.markup_processor.get_current()
            self.update()
        except ValueError as err_msg:
            print(f"Can't open the folder: {err_msg}")

    def set_answer(self, value: int):
        if value not in (-1, 1):
            raise ValueError(f"{value} is not in (-1, 1)")

        cur_i = self.current_element
        if not os.path.exists(cur_i.get("txt_path")):
            raise ValueError(f"{cur_i.get('folder_path')} does not exist")

        with open(cur_i["txt_path"], "w") as f_txt:
            key_words = "\t".join(cur_i["key_words"])
            f_txt.write(f"{cur_i['req_id']}\t{key_words}\t{cur_i['url']}\t{value}")

        self.markup_processor: MarkupProcess
        self.markup_processor.set_marked(cur_i.get("folder_path"))
        self.current_element = self.markup_processor.get_current()
        self.update()

    def update(self):
        self.update_status_bar()
        self.update_buttons()

        if self.markup_processor.need_markup_count > 0:
            print(f"Current element: {self.current_element}")
            self.update_picture()
            self.key_words.set(self.current_element.get("key_words"))
            self.url.set(self.current_element.get("url"))
        else:
            print(f"Folder {self.markup_folder} was marked")

    def update_status_bar(self):
        self.status_bar_string.set(
            f"Marked: {self.markup_processor.marked_count} | "
            f"Need: {self.markup_processor.need_markup_count} | "
            f"Total: {self.markup_processor.total_count}"
        )

    def update_buttons(self):
        if self.markup_processor.need_markup_count == 0:
            self.pass_button.config(state=tkinter.DISABLED)
            self.deny_button.config(state=tkinter.DISABLED)
        else:
            self.pass_button.config(state=tkinter.NORMAL)
            self.deny_button.config(state=tkinter.NORMAL)

    def update_picture(self):
        try:
            image = Image.open(self.current_element.get("img_path"))
            [img_w, img_h] = image.size
            while img_w > self.master.winfo_screenwidth() * 0.75 or img_h > self.master.winfo_screenheight() * 0.75:
                img_w, img_h = int(img_w * 0.75), int(img_h * 0.75)
            image = image.resize((img_w, img_h), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(image)
            self.canvas.configure(image=photo)
            self.canvas.image = photo
        except (UnidentifiedImageError, AttributeError):
            try:
                requests.get(self.current_element.get("url"))
                if self.current_element.get("img_path") is None:
                    res = "Image not found"
                else:
                    res = "Can't open"
            except requests.exceptions.RequestException as err:
                res = err
            self.canvas.configure(image='', text=res)
            self.canvas.image = None
            print(f"Can't open the image: {self.current_element.get('img_path')}")
            self.master.clipboard_clear()
            self.master.clipboard_append(self.current_element.get("url"))


if __name__ == '__main__':
    root = Tk()
    my_gui = MyFirstGUI(root)
    root.mainloop()
