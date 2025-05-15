import tkinter as tk

from PIL import Image, ImageTk
from tkinter import ttk



class Cluster:
    def __init__(self) -> None:
        pass

class ObjectMonitoring:
    
    @property
    def cluster(self) -> Cluster:
        return self._cluster
    
    @property
    def name(self) -> str:
        return self._name
    
    def set_name(self, name: str) -> None:
        self._name = name
    
    @property
    def show(self) -> bool:
        return self._show
    
    def set_show(self, show: bool) -> None:
        self._show = show
    
    def __init__(self, name: str = "", cluster: Cluster = None, show: bool = True) -> None:
        
        assert cluster is not None, "cluster must be provided"
        assert isinstance(cluster, Cluster), "cluster must be a Cluster instance"
        
        self._name = name
        self._cluster = cluster
        self._show = show


class ClusterMonitoring(ObjectMonitoring):
    @property
    def cluster(self) -> Cluster:
        return self._cluster
    
    def __init__(self, cluster = None) -> None:
        
        assert cluster is not None, "cluster must be provided"
        assert isinstance(cluster, Cluster), "cluster must be a Cluster instance"
        
        super().__init__(name="Lambda_0", cluster=cluster, show=False)
        self._cluster = cluster

class TkinterAthenaMonitoringApp:
    
    def load_file(self):
        # Implement file loading logic
        pass

    def save_file(self):
        # Implement file saving logic
        pass
    
    def minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def load_athena_icon(self) -> None:
        self.icon_image = Image.open("assets/athena.png")
        self.icon_image = self.icon_image.resize((32, 32), Image.LANCZOS)
        self.icon_photo = ImageTk.PhotoImage(self.icon_image)
        self.root.iconphoto(False, self.icon_photo)

    def set_fullscreen(self, fullscreen: bool) -> None:
        if fullscreen:
            self.root.state("zoomed")
        else:
            self.root.geometry(self._base_geometry)
            
    def move_window(self, event):
        self.root.geometry(f'+{event.x_root}+{event.y_root}')

    def resize_window(self, event):
        self.root.geometry(f'{event.x_root}x{event.y_root}') # add resize correctly !

    def close_window(self):
        self.root.destroy()
    
    def _UI_DA(self) -> None:
        # Style Root
        self.root.configure(bg="#4848F8")
        # Border with radius !!

        # Style Components
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#282c34")
        self.style.configure("TButton", background="#61afef", foreground="white", borderwidth=0)
        self.style.map("TButton",
                       background=[('active', '#56b6c2')],
                       relief=[('pressed', 'flat')])
        self.style.configure("TLabel", background="#282c34", foreground="white")
        
        
    def _BUILD_UTILS_FRAME(self) -> None:
        self._utils_bar = tk.Frame(self.root, bg="#4848F8", relief="raised", bd=2)
        self._utils_bar.pack(side="top", fill="x")
        
        self._utils_bar.bind('<B1-Motion>', self.move_window)
        
        self.load_athena_icon()
        self._icon_label = tk.Label(self._utils_bar, image=self.icon_photo, bg='#4848F8')
        self._icon_label.pack(side='left', padx=10)

        self._title_label = tk.Label(self._utils_bar, text='Athena', bg='#4848F8', fg='white', font=('Helvetica', 16, 'bold'))
        self._title_label.pack(side='left', padx=10)

        self._close_button = tk.Button(self._utils_bar, text='X', command=self.close_window, bg='#4848F8', fg='white', relief='flat')
        self._close_button.pack(side='right')
        
        self._reduce_button = tk.Button(self._utils_bar, text='-', command=self.minimize_window, bg='#4848F8', fg='white', relief='flat')
        self._reduce_button.pack(side='right')

        self._options_button = tk.Menubutton(self._utils_bar, text='Options', bg='#4848F8', fg='white', relief='flat')
        self._options_menu = tk.Menu(self._options_button, tearoff=0)
        self._options_menu.add_command(label="Load File", command=self.load_file)
        self._options_menu.add_command(label="Save File", command=self.save_file)
        self._options_button.config(menu=self._options_menu)
        self._options_button.pack(side='right')


    
    def _BUILD_TOP_FRAME(self) -> None:
        # No need to build the top frame now
        pass
        
    def _BUILD_MIDDLE_FRAME(self) -> None:
        pass
        
    def render(self) -> None:
        self.root.mainloop()
    
    def _pre_mount(self) -> None:
        # store the geometry of the window of the screen 1
        self._base_geometry = f'{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0'
    
    def __init__(self, params: dict = {
            "fullscreen": False,
        }) -> None:
    
        
        self._clusters = [
            ClusterMonitoring(cluster=Cluster())
        ]
        
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.title("Athena Monitoring")
        
        self._pre_mount()
        
        self.set_fullscreen(params["fullscreen"])
        self._UI_DA()
        self._BUILD_UTILS_FRAME()
        self._BUILD_TOP_FRAME()
        self._BUILD_MIDDLE_FRAME()
        
