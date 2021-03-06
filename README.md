# Gnome Extensions Loader

GUI to save and load gnome shell extensions and extension settings. This app makes it easier to share your gnome extensions setup with others. 

If an extension does not exist on the system, it will be downloaded from extensions.gnome.org website and installed automatically.

Config files and the downloaded extensions are stored in ~/.config/gnome-extensions-loader directory.

![](./assets/UI.png)

## Installation
### Build from the source
To install the app run the following commands in your terminal.
```
git clone https://github.com/emrecanaltinsoy/gnome-extensions-loader.git
cd gnome-extensions-loader
sudo make install
```

To uninstall the app run the following command in your terminal.
```
sudo make uninstall
```
### Install using deb package
After downloading the deb package go to the directory where it is located and run the following command.
```
sudo dpkg -i gnome-extensions-loader_1.0_amd64.deb
```

## Launch the app
To launch the app either run the following command on your terminal or run the application directly.
```
gnome-shell-extensions
```

## Features
- [x] Extension settings
- [ ] Keybindings
- [ ] Tweaks
