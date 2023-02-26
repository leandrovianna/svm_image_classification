import numpy as np
import cv2 as cv
from PIL import ImageTk, Image

import pathlib
import os
import math
import tkinter
from tkinter.constants import BOTH, LEFT


class ImageSelector:

    def __init__(self, positives_dir, negatives_dir):
        self.positives_dir = positives_dir
        self.negatives_dir = negatives_dir
        self.undefined_directory = None
        self.tk = None
        self.left_image_label = None
        self.right_image_label = None
        self.thumb_image_label = None
        self.information_label = None
        self.images = None
        self.current = None
        self.journal = None

    def build_button(self, frame, text, command, **kwargs):
        button = tkinter.Button(frame,
                                text=text,
                                font=50,
                                command=command,
                                **kwargs)
        return button

    def create_widgets(self):
        self.tk = tkinter.Tk()
        self.tk.protocol('WM_DELETE_WINDOW', self.close)
        self.tk.wm_attributes('-zoomed', True)
        self.tk.bind_all('<g>', lambda _: self.move_image(True))
        self.tk.bind_all('<p>', lambda _: self.move_image(True))
        self.tk.bind_all('<b>', lambda _: self.move_image(False))
        self.tk.bind_all('<n>', lambda _: self.move_image(False))
        self.tk.bind_all('<s>', lambda _: self.skip(1))
        self.tk.bind_all('<S>', lambda _: self.skip(10))
        self.tk.bind_all('<Control-s>', lambda _: self.skip(100))
        self.tk.bind_all('<u>', lambda _: self.undo())
        self.tk.bind_all('<q>', lambda _: self.close())

        main_frame = tkinter.Frame(self.tk, borderwidth=0)
        main_frame.pack(fill=BOTH)
        main_frame.bind('<Configure>', lambda e: self.update_ui())

        self.left_image_label = tkinter.Label(main_frame)
        self.left_image_label.grid(column=0, row=0, rowspan=2)

        self.right_image_label = tkinter.Label(main_frame)
        self.right_image_label.grid(column=1, row=0)

        self.thumb_image_label = tkinter.Label(main_frame)
        self.thumb_image_label.grid(column=1, row=1)

        self.information_label = tkinter.Label(main_frame, font=50)
        self.information_label.grid(column=0, row=2, columnspan=2)

        controls_frame = tkinter.Frame(main_frame)
        controls_frame.grid(column=0, row=3, columnspan=2)
        padding = {'padx': 10, 'pady': 10, 'ipadx': 25, 'ipady': 25}

        positive_button = self.build_button(controls_frame,
                                            'Positive',
                                            lambda: self.move_image(True),
                                            background='green',
                                            foreground='white',
                                            activebackground='dark green',
                                            activeforeground='white')
        positive_button.pack(side=LEFT, **padding)
        negative_button = self.build_button(controls_frame,
                                            'Negative',
                                            lambda: self.move_image(False),
                                            background='red',
                                            foreground='white',
                                            activebackground='dark red',
                                            activeforeground='white')
        negative_button.pack(side=LEFT, **padding)
        skip_button = self.build_button(controls_frame, 'Skip',
                                        lambda: self.skip(1))
        skip_button.pack(side=LEFT, **padding)
        skip_more_button = self.build_button(controls_frame, 'Skip 10',
                                             lambda: self.skip(10))
        skip_more_button.pack(side=LEFT, **padding)
        skip_much_more_button = self.build_button(controls_frame, 'Skip 100',
                                                  lambda: self.skip(100))
        skip_much_more_button.pack(side=LEFT, **padding)
        undo_button = self.build_button(controls_frame, 'Undo',
                                        lambda: self.undo())
        undo_button.pack(side=LEFT, **padding)

    def update_ui(self):
        if self.current < 0 or self.current >= len(self.images):
            return

        current_image = self.images[self.current]
        filename = os.path.basename(current_image)

        self.tk.title(f'{filename} ({self.current+1}/{len(self.images)})')
        win_width = self.tk.winfo_width()

        win_width = max(win_width, 100)

        image = Image.open(current_image)

        self.left_image_label.image = ImageTk.PhotoImage(
            self.image_resize(image, width=round(0.65 * win_width)))
        self.left_image_label.configure(image=self.left_image_label.image)
        self.right_image_label.image = ImageTk.PhotoImage(
            self.image_gradient(
                self.image_resize(image, width=round(0.35 * win_width))))
        self.right_image_label.configure(image=self.right_image_label.image)
        self.thumb_image_label.image = ImageTk.PhotoImage(
            self.image_resize(image, width=round(0.25 * win_width)))
        self.thumb_image_label.configure(image=self.thumb_image_label.image)
        self.information_label.configure(
            text=f'{filename} ({self.current+1}/{len(self.images)}) - ' +
            f'Brightness: {self.image_brightness(image)}/255 - ' +
            f'Contrast (Entropy): {self.image_contrast(image):.02f}')

    def next_image(self):
        self.current += 1
        while self.current < len(self.images) and not os.path.isfile(
                self.images[self.current]):
            self.journal.append(('not_found', None))
            self.current += 1

        if self.current == len(self.images):
            self.close()

    def move_image(self, is_positive):
        current_image = self.images[self.current]
        directory = self.positives_dir if is_positive else self.negatives_dir
        dest_img_path = os.path.join(directory,
                                     os.path.basename(current_image))
        if os.path.exists(dest_img_path):
            print('{os.path.basename(current_image)} already ' +
                  f'exists at {directory} directory.')
            self.journal.append(('skip', 1))
        else:
            os.rename(current_image, dest_img_path)
            self.journal.append(('move', dest_img_path))

        self.next_image()
        self.update_ui()

    def skip(self, count):
        self.journal.append(('skip', count))
        while count > 0:
            self.next_image()
            count -= 1
        self.update_ui()

    def undo(self):
        if len(self.journal) > 0:
            operation, param = self.journal.pop()
            if operation == 'skip':
                self.current -= param
            elif operation == 'move':
                os.rename(
                    param,
                    os.path.join(self.undefined_directory,
                                 os.path.basename(param)))
                self.current -= 1
            elif operation == 'not_found':
                self.current -= 1
                return self.undo()
            elif operation == 'begin':
                return self.close()

            self.update_ui()

    def close(self):
        self.tk.destroy()

    def select(self, directory):
        self.undefined_directory = directory
        imgs_dir = pathlib.Path(directory)
        image_files = [
            str(p) for p in imgs_dir.iterdir() if p.is_file() and (
                str(p).endswith('.jpg') or str(p).endswith('.png'))
        ]
        image_files.sort()

        self.images = image_files
        self.current = -1
        self.journal = [('begin', None)]

        self.create_widgets()
        self.next_image()
        self.update_ui()
        self.tk.mainloop()

    def image_brightness(self, image):
        gray_image = image.convert('L')
        value = np.mean(gray_image)
        return round(value)

    def image_resize(self, image, height=None, width=None):
        if height:
            zoom = height / image.size[1]
        elif width:
            zoom = width / image.size[0]
        return image.resize(tuple(round(x * zoom) for x in image.size))

    def image_gradient(self, image):
        im = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)

        gx = cv.Sobel(im, cv.CV_32F, 1, 0, ksize=1)
        gy = cv.Sobel(im, cv.CV_32F, 0, 1, ksize=1)
        mag, _ = cv.cartToPolar(gx, gy, angleInDegrees=True)

        mag = cv.normalize(mag, None, 255, 0, cv.NORM_MINMAX, cv.CV_8U)
        return Image.fromarray(cv.cvtColor(mag, cv.COLOR_BGR2RGB))

    def image_contrast(self, image):
        gray_image = image.convert('L')
        hist, _ = np.histogram(gray_image, bins=range(256), density=True)
        hist = hist[hist.nonzero()]
        entropy = -(hist * np.log(hist) / np.log(math.e)).sum()
        return entropy


if __name__ == '__main__':
    selector = ImageSelector('images/positives', 'images/negatives')
    selector.select('images/undefined')
