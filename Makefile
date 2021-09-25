PREFIX = /usr

all:
	@echo RUN \'make install\' to install Gnome extensions loader

install:
	@pip install -r requirements.txt
	@mkdir -p $(DESTDIR)$(PREFIX)/share/gnome-extensions-loader
	@cp -pr gnome-extensions-loader $(DESTDIR)$(PREFIX)/share
	@cp -p gnome-extensions-loader.desktop $(DESTDIR)$(PREFIX)/share/applications
	@chmod 755 $(DESTDIR)$(PREFIX)/share/gnome-extensions-loader/gnome-extensions-loader
	@ln -sf $(DESTDIR)$(PREFIX)/share/gnome-extensions-loader/gnome-extensions-loader $(DESTDIR)$(PREFIX)/bin/gnome-extensions-loader

uninstall:
	@rm -rf $(DESTDIR)$(PREFIX)/share/gnome-extensions-loader
	@rm $(DESTDIR)$(PREFIX)/bin/gnome-extensions-loader
	@rm $(DESTDIR)$(PREFIX)/share/applications/gnome-extensions-loader.desktop