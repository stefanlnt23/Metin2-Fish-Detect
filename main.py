import cv2
import pyautogui
from PIL import ImageGrab
import numpy as np
import pydirectinput
import time
import tkinter as tk
from tkinter import filedialog
import os
import sys
import webbrowser


paused = False
delay_time = 0


def prompt_user_for_coordinates():
    coordinates = []
    rect = None

    def on_mouse_press(event):
        nonlocal rect
        x, y = event.x, event.y
        coordinates.append(x)
        coordinates.append(y)

        if rect:
            canvas.delete(rect)

        rect = canvas.create_rectangle(x, y, x, y, outline="red", fill='green')

    def on_mouse_motion(event):
        nonlocal rect
        if len(coordinates) == 2:
            x1, y1 = coordinates
            x2, y2 = event.x, event.y
            canvas.coords(rect, x1, y1, x2, y2)

    def on_mouse_release(event):
        x, y = event.x, event.y
        coordinates.append(x)
        coordinates.append(y)
        if len(coordinates) == 4:
            window.destroy()

    window = tk.Tk()
    window.overrideredirect(True)  # Remove window decorations
    window.attributes("-alpha",0.1)  # Make the window transparent
    window.geometry("{0}x{1}+0+0".format(window.winfo_screenwidth(), window.winfo_screenheight()))  # Fullscreen

    label = tk.Label(window, text="Drag the area to select the region of interest.")
    label.pack(anchor='nw')

    canvas = tk.Canvas(window, bg=None, bd=0, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    window.bind("<ButtonPress-1>", on_mouse_press)
    window.bind("<B1-Motion>", on_mouse_motion)
    window.bind("<ButtonRelease-1>", on_mouse_release)
    window.bind("<Escape>", lambda e: window.destroy())
    window.focus_force()
    window.mainloop()

    return coordinates



def crop_screenshot(x1, y1, x2, y2):
    screenshot = ImageGrab.grab()
    cropped_screenshot = screenshot.crop((x1, y1, x2, y2))
    return np.array(cropped_screenshot)

def exit_program(control_window, root):
    control_window.destroy()
    root.destroy()
    os._exit(0)


def show_warning_message(message):
    warning_window = tk.Tk()
    warning_window.title("Warning")
    warning_window.geometry("300x100")

    warning_label = tk.Label(warning_window, text=message, wraplength=250)
    warning_label.pack(pady=10)

    ok_button = tk.Button(warning_window, text="Searching area", command=warning_window.destroy)
    ok_button.pack(pady=10)


def find_and_click_image(template_image_paths, cropped_screenshot, x1, y1):
    cropped_screenshot_gray = cv2.cvtColor(cropped_screenshot, cv2.COLOR_BGR2GRAY)
    image_found = False
    for template_image_path in template_image_paths:
        template = cv2.imread(template_image_path, 0)

        # Check if the template is smaller than the cropped_screenshot
        if template.shape[0] > cropped_screenshot_gray.shape[0] or template.shape[1] > cropped_screenshot_gray.shape[1]:
            message = f"Template image {template_image_path} is larger than the search area. Please use a smaller template image."
            show_warning_message(message)
            continue

        result = cv2.matchTemplate(cropped_screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > 0.8:
            x, y = max_loc
            x_center = x + template.shape[1] // 2
            y_center = y + template.shape[0] // 2
            pyautogui.click(x1 + x_center, y1 + y_center)
            image_found = True
            break

    return image_found


class Rubberband:
    def __init__(self, canvas, color="red", width=2):
        self.canvas = canvas
        self.color = color
        self.width = width
        self.start_x = None
        self.start_y = None
        self.rect_id = None

    def start(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if not self.rect_id:
            self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline=self.color, width=self.width)

    def extend(self, event):
        if not self.rect_id:
            return
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def stop(self, event):
        self.start_x = None
        self.start_y = None
        if self.rect_id:
            x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            self.canvas.master.return_coordinates(x1, y1, x2, y2)

class DraggableCanvas(tk.Canvas):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.rubberband = Rubberband(self)

    def on_click(self, event):
        self.rubberband.start(event)

    def on_drag(self, event):
        self.rubberband.extend(event)

    def on_release(self, event):
        self.rubberband.stop(event)

class AdjustArea(tk.Toplevel):
    def __init__(self, master, warning_message=None):
        super().__init__(master)
        self.title("Adjust Area")
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth(), self.winfo_screenheight()))
        self.canvas = DraggableCanvas(self, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        if warning_message:
            tk.messagebox.showwarning("Warning", warning_message)

        self.bind("<Escape>", lambda e: self.destroy())

    def return_coordinates(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.event_generate("<<CoordinatesUpdated>>")



class FishingBotGUI:
    class FishingBotGUI:
        def __init__(self, master):
            self.master = master
            master.title("Fishing Bot")
            master.geometry("400x400")


    def close_greetings_window(self):
        # Destroy the greetings_window and exit the program
        self.greetings_window.destroy()
        sys.exit()

    def pause(self):
        global paused
        paused = True
        self.pause_button.configure(bg='red')
        self.resume_button.configure(bg='white')

    def resume(self):
        global paused
        paused = False
        self.pause_button.configure(bg='white')
        self.resume_button.configure(bg='green')

    def show_greetings(self):
        self.greetings_window = tk.Tk()
        self.greetings_window.title("MENU")
        self.greetings_window.configure(bg='#4a4a4a')

        # Make the window non-resizable
        self.greetings_window.resizable(False, False)

        canvas = tk.Canvas(self.greetings_window, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Add the background image
        script_dir = get_script_directory()
        image_path = os.path.abspath(os.path.join(script_dir, "images", "bg.png"))
        background_image = tk.PhotoImage(file=image_path)

        canvas.create_image(0, 0, anchor="nw", image=background_image)

        # Add the "piecere" text
        piecere_label = tk.Label(canvas, text="", font=("Arial", 20), fg='red', bg='#4a4a4a')
        piecere_label.place(relx=0.5, rely=0.1, anchor='center')

        # Add the link button
        link_button = tk.Button(canvas, text="Instructions", font=("Arial", 12), bg='#2ecc71', fg='white',
                                command=lambda: webbrowser.open("https://youtu.be/yzfN_9WJEi4"))
        link_button.place(relx=0.18, rely=0.1, anchor='center')

        ok_button = tk.Button(canvas, text="Select area", command=lambda: self.greetings_window.destroy(), bg='#2ecc71',
                              fg='white', font=("Arial", 12))
        ok_button.place(relx=0.18, rely=0.24, anchor='center')
        self.greetings_window.protocol("WM_DELETE_WINDOW", self.close_greetings_window)
        # Set the size of the window to match the size of the background image
        self.greetings_window.geometry("%dx%d" % (background_image.width(), background_image.height()))

        self.greetings_window.mainloop()

    def start_program(self):
        self.greetings_window.destroy()

    def run(self):
        self.show_greetings()


def get_script_directory():
    return os.path.dirname(os.path.abspath(__file__))



def main():
    global paused, started

    # Show greetings window
    gui = FishingBotGUI()
    gui.run()

    # Prompt user for coordinates
    x1, y1, x2, y2 = prompt_user_for_coordinates()

    root = tk.Tk()
    root.withdraw()

    template_image_paths = filedialog.askopenfilenames(title="Select template images")
    if not template_image_paths:
        return

    # Create the control window

    def close_control_window():
        # Destroy the control_window and exit the program
        sys.exit()




    control_window = tk.Toplevel(root)
    control_window.title("Control")
    control_window.geometry("200x200")
    control_window.configure(bg='#4a4a4a')

    # Use a lambda function to wrap the close_control_window function call


    # Make the window non-resizable
    control_window.resizable(False, False)

    canvas = tk.Canvas(control_window, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Add the background image
    if getattr(sys, 'frozen', False):
        # If the script is running in a PyInstaller bundle
        base_dir = sys._MEIPASS
    else:
        # If the script is not bundled
        base_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = get_script_directory()
    image_path = os.path.join(base_dir, "images", "bg.png")
    background_image = tk.PhotoImage(file=image_path)

    canvas.create_image(0, 0, anchor="nw", image=background_image)

    # Add the "piecere" text
    piecere_label = tk.Label(canvas, text="", font=("Arial", 20), fg='red', bg='#4a4a4a')
    piecere_label.place(relx=0.5, rely=0.1, anchor='center')

    # Set the size of the window to match the size of the background image
    control_window.geometry("%dx%d" % (background_image.width(), background_image.height()))

    paused = False
    started = False

    def on_scale_changed(value):
        global delay_time
        delay_time = float(value)
        print("Delay time changed:", delay_time)

    def pause():
        global paused
        paused = True
        start_button.config(bg='green')
        pause_button.config(bg='orange')
        resume_button.config(bg='green')

    def resume():
        global paused
        paused = False
        start_button.config(bg='green')
        pause_button.config(bg='green')
        resume_button.config(bg='orange')

    def start():
        global started
        started = True
        start_button.config(bg='orange')
        pause_button.config(bg='green')
        resume_button.config(bg='green')

    def exit_program(control_window, root):
        control_window.destroy()
        root.destroy()
        os._exit(0)

    exit_button = tk.Button(control_window, text="Exit", command=lambda: exit_program(control_window, root), width=10,
                            background='red')
    exit_button.place(relx=0.85, rely=0.95, anchor='center')

    control_window.protocol("WM_DELETE_WINDOW", root.destroy)

    start_button = tk.Button(control_window, text="Start", command=start, width=10, bg='green')
    start_button.place(relx=0.1, rely=0.05, anchor='center')

    pause_button = tk.Button(control_window, text="Pause", command=pause, width=10, bg='green')
    pause_button.place(relx=0.1, rely=0.2, anchor='center')

    resume_button = tk.Button(control_window, text="Resume", command=resume, width=10, bg='green')
    resume_button.place(relx=0.1, rely=0.3, anchor='center')
    scale_bar = tk.Scale(control_window, from_=0, to=20, orient=tk.VERTICAL, command=on_scale_changed,background='grey')
    scale_label = tk.Label(canvas, text="DELAY", font=("Arial", 10), fg='white', bg='#4a4a4a')
    scale_label.place(relx=0.07, rely=0.58, anchor='center')
    scale_bar.place(relx=0.07, rely=0.8, anchor='center')

    start_time = time.time()

    image_found = False
    while True:


        root.update_idletasks()
        root.update()

        if started and not paused:
            if time.time() - start_time < delay_time:
                cropped_screenshot = crop_screenshot(x1, y1, x2, y2)
                image_found = find_and_click_image(template_image_paths, cropped_screenshot, x1, y1)
                if image_found:
                    start_time = time.time()
            else:
                if not image_found:
                    pydirectinput.press('1')
                    pydirectinput.press('space')

                # Reset variables for the next iteration
                start_time = time.time()
                image_found = False


if __name__ == "__main__":
    main()

