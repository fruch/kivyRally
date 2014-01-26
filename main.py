import kivy
kivy.require('1.7.2')
from kivy.config import Config

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from extra.storage.jsonstore import JsonStore

# remove this when on real device
#Config.set('graphics', 'width', str(768 / 2))
#Config.set('graphics', 'height',str(1024 / 2))

import pyral

#TODO: fix the setup screen no to connect on default
#TODO: spinner icon when checking connection
#TODO: get the task list from rally, and show it in a view
#TODO: tree view for the projects
#TODO: add defect/story screen
#TODO: make the connection creation async, it slow down the first screen
#TODO: write breadcrumbs for the ScreenManager by override the on_current function

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.

Builder.load_string("""
[HSeparator@Label]:
    size_hint_y: None
    height: max(dp(45), self.texture_size[1] + dp(10))
    text: ctx.text if 'text' in ctx else ''
    text_size: self.width, None
    valign: 'middle'
    halign: 'center'
    canvas.before:
        Color:
            rgba: .2, .2, .2, .8
        Rectangle:
            size: self.size
            pos: self.pos

<MenuScreen>:
    BoxLayout:
        orientation: 'vertical'
        Button:
            text: 'Tasks'
            on_press: root.manager.current = 'tasks'
        Button:
            text: 'Stories'
            on_press: root.manager.current = 'stories'
        Button:
            text: 'Defects'
            on_press: root.manager.current = 'defects'

        Button:
            text: 'Settings'
            on_press: root.manager.current = 'settings'
        Button:
            text: 'Quit'

<DefectsScreen>:
    BoxLayout:
        orientation: 'vertical'
        ListView:
            id: defects_list
            size_hint: 1, 1
            item_strings: []

<TasksScreen>:
    BoxLayout:
        orientation: 'vertical'
        ListView:
            id: tasks_list
            size_hint: 1, 1
            item_strings: [str("TASK number 1 and more %d" % index) for index in range(100)]

<SettingsScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10

        HSeparator:
            text: 'Login'

        BoxLayout:
            size_hint: 1, None
            height: dp(50)
            orientation: 'horizontal'
            Label:
                text: 'Username'
                font_size: '16sp'
                size_hint_x: 0.3
            TextInput:
                id: username
                font_size: '18sp'
                size_hin_x: 0.8

        BoxLayout:
            size_hint: 1, None
            height: dp(50)
            orientation: 'horizontal'
            Label:
                text: 'Password'
                font_size: '16sp'
                size_hint_x: 0.3
            TextInput:
                id: password
                font_size: '18sp'
                size_hin_x: 0.8
                password: True

        Button:
            id: connection_button
            size_hint: 1, None
            height: dp(50)
            text: 'Check Connection'
            on_press: root.check_connection()

        HSeparator:
            text: 'Defaults'

        BoxLayout:
            size_hint: 1, None
            height: dp(50)
            orientation: 'horizontal'
            Label:
                text: 'Workspace'
                font_size: '16sp'
                size_hint_x: 0.3
            Spinner:
                id: workspaces
                text: "None"
                values: "Work",

        BoxLayout:
            size_hint: 1, None
            height: dp(50)
            orientation: 'horizontal'
            Label:
                text: 'Project'
                font_size: '16sp'
                size_hint_x: 0.3
            Spinner:
                id: projects
                text: "None"
                values: "None",

        BoxLayout:
            orientation: 'horizontal'
            padding: 10
            spacing: 10
            Button:
                size_hint: 1, None
                height: dp(50)
                text: 'Back'
                on_press: root.manager.current = 'menu'

            Button:
                size_hint: 1, None
                height: dp(50)
                text: 'Save'
                on_press:
                    root.do_save_settings()
                    root.manager.current = 'menu'
                size_hin_x: 0.8

""")

class MainConnection(object):
    connected = False
    work_spaces = dict()
    subscription = ""

    @classmethod
    def connect(cls, username=None, password=None, workspace=None, project=None):
        if username is None:
            username = SETTINGS.get("settings")['username']
            password = SETTINGS.get("settings")['password']
            workspace = SETTINGS.get("settings")['workspace']
            project = SETTINGS.get("settings")['project']
            cls.rally = pyral.Rally("rally1.rallydev.com", username,
                                    password, project=project, workspace=workspace)
        else:
            cls.rally = pyral.Rally("rally1.rallydev.com", username, password)

        cls.results = cls.rally.get('Subscription', fetch="Workspaces,Name,Projects")
        cls.connected = True

    @classmethod
    def get_workspaces_and_project(cls):
        results = cls.rally.get('Subscription', fetch="Workspaces,Name,Projects")

        # save the work spaces and projects
        for result in results:
            cls.subscription = result.Name
            for workspace in result.Workspaces:
                cls.work_spaces[workspace.Name] = []
                for project in  workspace.Projects:
                    cls.work_spaces[workspace.Name].append(project.Name)


SETTINGS = JsonStore('settings.json')
if not SETTINGS.exists("settings"):
    SETTINGS.put("settings")


class TasksScreen(Screen):
    def __init__(self, *args, **kwargs):

        super(TasksScreen, self).__init__(*args, **kwargs)

    def on_enter(self, *args, **kwargs):
        super(TasksScreen, self).on_enter(*args, **kwargs)

        MainConnection.connect()
        user = MainConnection.rally.getUserInfo(username=SETTINGS.get("settings")['username'] ).pop(0)
        query =  dict(Owner=user.ref)
        res = MainConnection.rally.get('Task', fetch=True, query=query)
        print res
        self.ids.tasks_list.item_strings = []
        for r in res:
            print r.Name
            self.ids.tasks_list.item_strings.append(r.Name)


class StoriesScreen(Screen):
    pass

class DefectsScreen(Screen):
    def on_enter(self, *args, **kwargs):
        super(DefectsScreen, self).on_enter(*args, **kwargs)

        MainConnection.connect()
        user = MainConnection.rally.getUserInfo(username=SETTINGS.get("settings")['username'] ).pop(0)
        query =  dict(Owner=user.ref)
        res = MainConnection.rally.get('Defect', fetch=True, query=query)
        print res
        self.ids.defects_list.item_strings = []
        for r in res:
            print r.Name
            self.ids.defects_list.item_strings.append(r.Name)


# Declare both screens
class MenuScreen(Screen):
    pass

class SettingsScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(SettingsScreen, self).__init__(*args, **kwargs)

        settings = SETTINGS.get("settings")
        self.ids.username.text = settings.get("username", "")
        self.ids.password.text = settings.get("password", "")
        self.ids.workspaces.text = settings.get("workspace", "-- None Selected --")
        self.ids.projects.text = settings.get("project", "-- None Selected --")

    def on_enter(self, *args):
        if not MainConnection.connected:
            self.check_connection()

        if MainConnection.connected:
            self.populate_workspaces_and_projects()

        self.ids.workspaces.bind(text=self.select_workspace)
        super(SettingsScreen, self).on_enter(*args)

    def select_workspace(self, obj, text):
        if text == "-- None Selected --":
            values = []
        else:
            values = MainConnection.work_spaces[str(text)]
        self.ids.projects.values = ["-- None Selected --", ] + values

    def check_connection(self):
        try:
            MainConnection.connect( username=self.ids.username.text,
                                password=self.ids.password.text)

            self.ids.connection_button.background_color = [0, 1, 0, 1]
            return True

        except Exception as e:
            error_content = Label(text=str(e))
            popup = Popup(title='Connection Error',
                content=error_content, size_hint=[1, 0.5])
            error_content.bind(on_press=popup.dismiss)
            popup.open()
            self.ids.connection_button.background_color = [1, 0, 0, 1]


    def populate_workspaces_and_projects(self):
        MainConnection.get_workspaces_and_project()
        workspaces_spinner = self.ids.workspaces
        workspaces_spinner.values = ["-- None Selected --", ] + MainConnection.work_spaces.keys()

    def do_save_settings(self):
        SETTINGS.put('settings',
            username = self.ids.username.text,
            password = self.ids.password.text,
            workspace = self.ids.workspaces.text,
            project = self.ids.projects.text
        )

from kivy.utils import platform
from kivy.core.window import Window

class RallyApp(App):

    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(TasksScreen(name='tasks'))
        sm.add_widget(StoriesScreen(name='stories'))
        sm.add_widget(DefectsScreen(name='defects'))

        self.manager = sm
        self.bind(on_start=self.post_build_init)
        return sm

    def post_build_init(self, *args):
        if platform() == 'android':
            import android
            android.map_key(android.KEYCODE_BACK, 1001)

        win = Window
        win.bind(on_keyboard=self.my_key_handler)

    def my_key_handler(self, window, keycode1, keycode2, text, modifiers):
        if keycode1 in [27, 1001]:
            self.manager.current = 'menu'
            return True
        return False

if __name__ == '__main__':
    RallyApp().run()