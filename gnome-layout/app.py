#!/usr/bin/python3

import ast
import configparser
import os
import re
import subprocess
import sys
from glob import glob

from PyQt5.QtWidgets import (
    QApplication,
    QInputDialog,
    QMainWindow,
    QMessageBox,
)

from ui.app_ui import Ui_MainWindow
from utils.download_extension import download_extension

LAYOUT_DIR = "/home/emrecan/.config/layouts"


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setFixedSize(250, 300)
        self.connectSignalsSlots()
        self.view_conf_files()

        self.config = configparser.ConfigParser()
        self.shell_version = get_shell_version()
        self.session = get_session_type()

    def connectSignalsSlots(self):
        self.action_Add.triggered.connect(self.add_layout)
        self.action_Remove.triggered.connect(self.remove_layout)
        self.action_About.triggered.connect(show_about)
        self.action_Overwrite.triggered.connect(self.overwrite_layout)
        self.action_Apply.triggered.connect(self.apply_layout)
        self.action_Exit.triggered.connect(self.close)

    def apply_layout(self):
        listItems = self.listWidget.selectedItems()
        if not listItems:
            show_message(
                message="Select a layout to apply.",
                title="Apply Layout",
                style="warning",
            )
            return

        for item in listItems:
            self.config.read(f"{LAYOUT_DIR}/{item.text()}.conf")

            (
                extensions_to_enable,
                extensions_to_disable,
                missing_extensions,
            ) = self.check_extensions()

            verify_installation = self.pre_installation_message(
                extensions_to_enable, extensions_to_disable, missing_extensions
            )

            if verify_installation == QMessageBox.Ok:
                (
                    installation_success,
                    installation_fail,
                ) = self.install_missing_extensions(missing_extensions)
                bash_command(
                    ["./utils/load_conf.sh", f"{item.text()}", f"{LAYOUT_DIR}"]
                )

                post_installation_message = self.post_installation_message(
                    installation_success,
                    installation_fail,
                    extensions_to_enable,
                    extensions_to_disable,
                )

                if post_installation_message:
                    show_message(
                        message=f"{post_installation_message}",
                        title="Applied Changes",
                        style="information",
                    )
                if installation_success:
                    if re.search("wayland", self.session):
                        show_message(
                            message="You may need to log out for the changes to take effect.",
                            title="Log out",
                            style="information",
                        )
                    else:
                        answer = show_message(
                            message="Would you like to restart gnome shell?",
                            title="Restart Shell",
                            style="question",
                        )
                        if answer == QMessageBox.Ok:
                            bash_command(["./utils/restart_shell.sh"])

    def add_layout(self):
        text, ok = QInputDialog.getText(
            self, "Add Layout", "Enter the name of your layout:"
        )
        if ok:
            if text:
                if not os.path.isfile(f"{LAYOUT_DIR}/{str(text)}.conf"):
                    self.listWidget.addItem(str(text))
                    bash_command(["./utils/dump_conf.sh", f"{text}", f"{LAYOUT_DIR}"])
                else:
                    show_message(
                        message="Layout name exists!",
                        title="Existing Name",
                        style="warning",
                    )
            else:
                show_message(
                    message="Layout name is missing!",
                    title="Missing Name",
                    style="warning",
                )

    def overwrite_layout(self):
        listItems = self.listWidget.selectedItems()
        if not listItems:
            show_message(
                message="Select a layout to overwrite.",
                title="Overwrite Layout",
                style="warning",
            )
            return

        answer = show_message(
            message="Are you sure?", title="Owerwrite Layout", style="question"
        )
        if answer == QMessageBox.Ok:
            for item in listItems:
                bash_command(
                    ["./utils/dump_conf.sh", f"{item.text()}", f"{LAYOUT_DIR}"]
                )
                show_message(
                    message="Layout overwritten successfully.",
                    title="Overwrite Layout",
                    style="information",
                )

    def install_missing_extensions(self, missing_extensions):
        installation_fail = set()
        installation_success = set()

        for uuid in missing_extensions:
            check_download = download_extension(LAYOUT_DIR, uuid, self.shell_version)
            if check_download:
                bash_command(
                    ["./utils/install_extension.sh", f"{uuid}", f"{LAYOUT_DIR}"]
                )
                installation_success.add(uuid)
            else:
                installation_fail.add(uuid)

        return installation_success, installation_fail

    def pre_installation_message(
        self, extensions_to_enable, extensions_to_disable, missing_extensions
    ):
        # print("MISSING\n", missing_extensions)
        # print("ENABLE\n", extensions_to_enable)
        # print("DISABLE\n", extensions_to_disable)
        message = ""
        if missing_extensions:
            message += "Extensions to Install:"
            for uuid in missing_extensions:
                if uuid:
                    message += f"\n- {uuid.split('@')[0]}"

            if extensions_to_enable or extensions_to_disable:
                message += "\n\n"

        if extensions_to_enable:
            message += "Extensions to Enable:"
            for uuid in extensions_to_enable:
                if uuid:
                    message += f"\n- {uuid.split('@')[0]}"

            if extensions_to_disable:
                message += "\n\n"

        if extensions_to_disable:
            message += "Extensions to Disable:"
            for uuid in extensions_to_disable:
                if uuid:
                    message += f"\n- {uuid.split('@')[0]}"

        if message:
            return show_message(
                message=f"{message}",
                title="Extensions",
                style="question",
            )
        return QMessageBox.Ok

    def post_installation_message(
        self,
        installation_success,
        installation_fail,
        extensions_to_enable,
        extensions_to_disable,
    ):
        post_installation_message = ""
        if installation_success:
            post_installation_message += "Installed:"
            for uuid in installation_success:
                post_installation_message += f"\n- {uuid.split('@')[0]}"
            if installation_fail or extensions_to_enable or extensions_to_disable:
                post_installation_message += "\n\n"
            # print("INSTALLED\n", installation_success)

        if installation_fail:
            post_installation_message += "Failed to Install:"
            for uuid in installation_fail:
                post_installation_message += f"\n- {uuid.split('@')[0]}"
            if extensions_to_enable or extensions_to_disable:
                post_installation_message += "\n\n"
            # print("FAILED TO INSTALL\n", installation_fail)

        extensions_to_enable = extensions_to_enable.difference(installation_fail)
        if extensions_to_enable:
            post_installation_message += "Enabled:"
            for uuid in extensions_to_enable:
                post_installation_message += f"\n- {uuid.split('@')[0]}"
            if extensions_to_disable:
                post_installation_message += "\n\n"
            # print("ENABLED\n", extensions_to_enable)

        if extensions_to_disable:
            post_installation_message += "Disabled:"
            for uuid in extensions_to_disable:
                post_installation_message += f"\n- {uuid.split('@')[0]}"
            # print("DISABLED\n", extensions_to_disable)

        return post_installation_message

    def check_extensions(self):
        to_be_enabled = set(
            ast.literal_eval(self.config.get("/", "enabled-extensions"))
        )
        currently_enabled = set(enabled_extensions())
        installed_extensions = set(all_extensions())

        to_be_enabled.discard("")
        currently_enabled.discard("")
        installed_extensions.discard("")

        missing_extensions = to_be_enabled.difference(installed_extensions)
        extensions_to_enable = to_be_enabled.difference(currently_enabled)
        extensions_to_disable = currently_enabled.difference(to_be_enabled)

        return extensions_to_enable, extensions_to_disable, missing_extensions

    def remove_layout(self):
        listItems = self.listWidget.selectedItems()
        if not listItems:
            show_message(
                message="Select a layout to remove.",
                title="Remove Layout",
                style="warning",
            )
            return

        answer = show_message(
            message="Are you sure?", title="Remove Layout", style="question"
        )
        if answer == QMessageBox.Ok:
            for item in listItems:
                self.listWidget.takeItem(self.listWidget.row(item))
                bash_command(["rm", f"{LAYOUT_DIR}/{item.text()}.conf"])

    def view_conf_files(self):
        conf_files = glob(f"{LAYOUT_DIR}/*.conf")
        conf_file_names = [i.split("/")[-1].split(".")[0] for i in conf_files]
        for name in conf_file_names:
            self.listWidget.addItem(name)


def all_extensions():
    return bash_command(["gnome-extensions", "list"]).split("\n")


def enabled_extensions():
    return bash_command(["gnome-extensions", "list", "--enabled"]).split("\n")


def disabled_extensions():
    return bash_command(["gnome-extensions", "list", "--disabled"]).split("\n")


def bash_command(bashCmd):
    with subprocess.Popen(bashCmd, stdout=subprocess.PIPE) as process:
        output, error = process.communicate()
        if not error:
            return output.decode("utf-8")
    return None


def get_shell_version():
    shell = bash_command(["gnome-shell", "--version"])
    shell = re.sub("[^0-9.]", "", shell).split(".")
    return ".".join(shell[0:2])


def get_session_type():
    session = bash_command(["./utils/get_session.sh"])
    return session


def show_about():
    show_message(
        message="<p>Gnome layout saver/loader app:</p>"
        "<p>Version: 1.0</p>"
        "<p>Emrecan Altinsoy</p>"
        "<p>emrecanaltinsoy@yahoo.com.tr</p>",
        title="About",
        style="information",
    )


def show_message(message=None, title=None, style=None):
    msgBox = QMessageBox()
    if style == "critical":
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setStandardButtons(QMessageBox.Ok)
    elif style == "question":
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    elif style == "information":
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setStandardButtons(QMessageBox.Ok)
    elif style == "warning":
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.setText(message)
    msgBox.setWindowTitle(title)
    return msgBox.exec()


if __name__ == "__main__":
    os.makedirs(f"{LAYOUT_DIR}", exist_ok=True)
    os.makedirs(f"{LAYOUT_DIR}/extensions", exist_ok=True)
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
