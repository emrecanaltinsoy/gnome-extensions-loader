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

from app_ui import Ui_MainWindow
from src.download_extension import download_extension

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
        self.extensions_to_enable = None

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
            verify_installation = self.install_missing_extensions()
            if verify_installation == QMessageBox.Ok:
                disabled = self.disable_extensions()
                enabled = self.enable_extensions()
                bash_command(["./src/load_conf.sh", f"{item.text()}", f"{LAYOUT_DIR}"])
                bash_command(["./src/restart_shell.sh"])

                message = self.enabled_disabled_message(enabled, disabled)
                show_message(
                    message=message,
                    title="Enabled/Disabled Extensions",
                    style="information",
                )

    def add_layout(self):
        text, ok = QInputDialog.getText(
            self, "Add Layout", "Enter the name of your layout:"
        )
        if ok:
            if text:
                if not os.path.isfile(f"{LAYOUT_DIR}/{str(text)}.conf"):
                    self.listWidget.addItem(str(text))
                    bash_command(["./src/dump_conf.sh", f"{text}", f"{LAYOUT_DIR}"])
                else:
                    show_message(
                        message="Layout name exists!", title=None, style="warning"
                    )
            else:
                show_message(
                    message="Layout name is missing!", title=None, style="warning"
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
                bash_command(["./src/dump_conf.sh", f"{item.text()}", f"{LAYOUT_DIR}"])
                show_message(
                    message="Layout overwritten successfully.",
                    title="Overwrite Layout",
                    style="information",
                )

    def install_missing_extensions(self):
        self.extensions_to_enable = ast.literal_eval(
            self.config.get("/", "enabled-extensions")
        )
        missing_extensions = set(self.extensions_to_enable).difference(
            set(all_extensions())
        )

        if missing_extensions:
            verify_message = "Following extensions will be installed."
            for uuid in missing_extensions:
                verify_message += f"\n- {uuid.split('@')[0]}"

            verify_installation = show_message(
                message=f"{verify_message}",
                title="Extensions",
                style="question",
            )

            installation_fail = []
            installation_success = []

            if verify_installation == QMessageBox.Ok:
                for uuid in missing_extensions:
                    check_download = download_extension(
                        LAYOUT_DIR, uuid, self.shell_version
                    )
                    if check_download:
                        bash_command(
                            ["./src/install_extension.sh", f"{uuid}", f"{LAYOUT_DIR}"]
                        )
                        installation_success.append(uuid.split("@")[0])
                    else:
                        installation_fail.append(uuid.split("@")[0])

                post_installation_message = self.installation_message(
                    installation_success, installation_fail
                )

                show_message(
                    message=f"{post_installation_message}",
                    title="Extension Installation",
                    style="information",
                )

            return verify_installation

        return QMessageBox.Ok

    def installation_message(self, installation_success, installation_fail):
        post_installation_message = ""
        if installation_success:
            post_installation_message += "Installed:"
            for uuid in installation_success:
                post_installation_message += f"\n- {uuid}"
            post_installation_message += "\n\n"
            print("INSTALLED\n", installation_success)

        if installation_fail:
            post_installation_message += "Failed:"
            for uuid in installation_fail:
                post_installation_message += f"\n- {uuid}"
            print("FAILED TO INSTALL\n", installation_fail)

        return post_installation_message

    def enabled_disabled_message(self, enabled, disabled):
        message = ""
        if enabled:
            message += "Enabled:"
            for uuid in enabled:
                message += f"\n- {uuid}"
            print("ENABLED\n", enabled)
        if enabled and disabled:
            message += "\n\n"
        if disabled:
            message += "Disabled:"
            for uuid in disabled:
                message += f"\n- {uuid}"
            print("DISABLED\n", disabled)

        return message

    def disable_extensions(self):
        extensions_to_disable = set(enabled_extensions()).difference(
            set(self.extensions_to_enable)
        )
        disabled = []
        for e in extensions_to_disable:
            if e:
                bash_command(["gnome-extensions", "disable", f"{e}"])
                disabled.append(e)
        if disabled:
            return disabled
        return None

    def enable_extensions(self):
        enabled = []
        for e in set(disabled_extensions()).intersection(
            set(self.extensions_to_enable)
        ):
            if e:
                bash_command(["gnome-extensions", "enable", f"{e}"])
                enabled.append(e)
        if enabled:
            return enabled
        return None

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
    process = subprocess.Popen(bashCmd, stdout=subprocess.PIPE)
    output, error = process.communicate()
    if not error:
        return output.decode("utf-8")
    return None


def get_shell_version():
    shell = bash_command(["gnome-shell", "--version"])
    shell = re.sub("[^0-9.]", "", shell).split(".")
    return ".".join(shell[0:2])


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
