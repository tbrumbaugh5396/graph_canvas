#!/usr/bin/env python3
"""
Create macOS Application Bundle for Graph Canvas (Graph Editor)
Generates a complete .app bundle that can be double-clicked to launch
"""

import os
import shutil
import stat
import plistlib
from pathlib import Path
import sys


def create_app_bundle():
	"""Create a complete macOS application bundle"""

	app_name = "Graph Canvas"
	bundle_name = f"{app_name}.app"

	# Determine project root (repo root), independent of current working directory
	root = Path(__file__).resolve().parent.parent

	# Remove existing bundle if it exists (in project root)
	bundle_path = root / bundle_name
	if bundle_path.exists():
		shutil.rmtree(bundle_path)

	# Create bundle directory structure
	contents_path = bundle_path / "Contents"
	macos_path = contents_path / "MacOS"
	resources_path = contents_path / "Resources"

	# Create directories
	macos_path.mkdir(parents=True, exist_ok=True)
	resources_path.mkdir(parents=True, exist_ok=True)

	# Copy entire src tree so the bundle has the full code
	src_path = root / "src"
	if src_path.exists():
		shutil.copytree(src_path, resources_path / "src")
	else:
		print("⚠️  'src/' directory not found; bundle may be incomplete.")

	# Copy top-level entry files required by the launcher (they now live in src)
	for top_file in ["main.py", "app.py"]:
		path = src_path / top_file
		if path.exists():
			shutil.copy2(path, resources_path / top_file)
		else:
			print(f"⚠️  '{top_file}' not found inside src/; ensure the entrypoint exists.")

	# Always include helpful files
	for file in ["requirements.txt", "README.md", "custom_themes.json"]:
		if (root / file).exists():
			shutil.copy2(root / file, resources_path)

	# Use the current Python interpreter for the shebang and pip vendor install
	python_exec = sys.executable or "/usr/bin/env python3"

	# Vendor dependencies into Resources/vendor using pip so the app can run standalone
	vendor_dir = resources_path / "vendor"
	if vendor_dir.exists():
		shutil.rmtree(vendor_dir)
	vendor_dir.mkdir(exist_ok=True)

	requirements_file = root / "requirements.txt"
	if requirements_file.exists():
		try:
			import subprocess
			print("📦 Installing Python dependencies into app bundle vendor directory (no-deps)...")
			# Use the same interpreter that will run the launcher
			subprocess.run([
				python_exec, "-m", "pip", "install",
				"-r", str(requirements_file),
				"-t", str(vendor_dir),
				"--upgrade",
				"--no-deps",
				"--no-input",
				"--disable-pip-version-check"
			], check=True)
			print("✅ Dependencies installed into Resources/vendor")
		except Exception as e:
			print(f"⚠️  Failed to vendor dependencies: {e}")

	# Copy database if it exists (so the app can start with data)
	if (root / "kanban.db").exists():
		shutil.copy2(root / "kanban.db", resources_path)

	# Copy icons
	icons_src = root / "icons"
	if icons_src.exists():
		shutil.copytree(icons_src, resources_path / "icons")

	# Copy sample/data directory if present
	data_src = root / "data"
	if data_src.exists():
		shutil.copytree(data_src, resources_path / "data")

	# Use the current Python interpreter for the shebang so Finder can launch it

	# Create the main executable launcher script (Python)
	launcher_body = """import sys
import os
import traceback

# Paths inside the .app bundle
app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
resources_path = os.path.join(app_path, "Resources")
vendor_path = os.path.join(resources_path, "vendor")

def log(msg):
    try:
        with open(os.path.join(resources_path, "launch.log"), "a") as f:
            f.write(str(msg) + "\\n")
    except Exception:
        pass

# Ensure we can import from Resources/src
if resources_path not in sys.path:
    sys.path.insert(0, resources_path)
src_path = os.path.join(resources_path, "src")
if os.path.isdir(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)
if os.path.isdir(vendor_path) and vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

# Change to Resources so relative files (db, configs, icons) resolve
os.chdir(resources_path)

log("Launcher starting...")
log(f"sys.executable: {sys.executable}")
log(f"cwd: {os.getcwd()}")

try:
    # Launch application main entrypoint
    import main
    log("Imported main module")
    if hasattr(main, "main"):
        log("Calling main.main()")
        main.main()
    else:
        # Fallback: try starting wx app directly
        log("Falling back to wx App launch")
        import wx
        from graph_canvas.presentation.desktop.gui.main_window import MainWindow
        app = wx.App(False)
        win = MainWindow()
        win.Show()
        app.MainLoop()
except Exception as e:
    tb = traceback.format_exc()
    log("Unhandled exception during launch:\\n" + tb)
    # Show a simple GUI error dialog using tkinter (no terminal when double-clicking)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Failed to start application:\\n{e}")
        root.destroy()
    except Exception:
        # Last resort: write to a log file in Resources
        try:
            with open(os.path.join(resources_path, "launch_error.log"), "a") as f:
                f.write(tb + "\\n")
        except Exception:
            pass
"""
	launcher_script = f"#!{python_exec}\n" + launcher_body

	# Write the launcher script
	launcher_path = macos_path / app_name.replace(" ", "")
	with open(launcher_path, 'w') as f:
		f.write(launcher_script)

	# Make the launcher executable
	st = os.stat(launcher_path)
	os.chmod(launcher_path, st.st_mode | stat.S_IEXEC)

	# Create Info.plist
	plist_data = {
		'CFBundleName': app_name,
		'CFBundleDisplayName': app_name,
		'CFBundleIdentifier': 'com.graphcanvas.app',
		'CFBundleVersion': '1.0.0',
		'CFBundleShortVersionString': '1.0.0',
		'CFBundleExecutable': app_name.replace(" ", ""),
		'CFBundleIconFile': 'graph_canvas.icns',
		'CFBundlePackageType': 'APPL',
		'CFBundleSignature': '????',
		'LSMinimumSystemVersion': '10.13.0',
		'NSHighResolutionCapable': True,
		'NSSupportsAutomaticGraphicsSwitching': True,
		'NSRequiresAquaSystemAppearance': False,
		'LSApplicationCategoryType': 'public.app-category.productivity',
	}

	# Write Info.plist
	with open(contents_path / "Info.plist", 'wb') as f:
		plistlib.dump(plist_data, f)

	# Convert PNG icon to ICNS if possible
	create_icns_icon(resources_path)

	print(f"✅ Created {bundle_name}")
	print(f"📁 Bundle location: {bundle_path.resolve()}")
	print(f"🚀 Double-click {bundle_name} to launch the application")
	print(f"📋 You can drag {bundle_name} to Applications folder or Dock")

	return bundle_name



def create_icns_icon(resources_path):
	"""Create ICNS icon file from PNG icons"""

	icons_dir = resources_path / "icons"
	if not icons_dir.exists():
		print("⚠️  Icons directory not found, using default icon")
		return

	# Try to use iconutil (macOS built-in tool)
	try:
		import subprocess

		# Create iconset directory
		iconset_dir = resources_path / "kanban_icon.iconset"
		iconset_dir.mkdir(exist_ok=True)

		# Icon size mappings for macOS
		icon_mappings = {
			'icon_16x16.png': 'graph_canvas_16x16.png',
			'icon_16x16@2x.png': 'graph_canvas_32x32.png',
			'icon_32x32.png': 'graph_canvas_32x32.png',
			'icon_32x32@2x.png': 'graph_canvas_64x64.png',
			'icon_128x128.png': 'graph_canvas_128x128.png',
			'icon_128x128@2x.png': 'graph_canvas_256x256.png',
			'icon_256x256.png': 'graph_canvas_256x256.png',
			'icon_256x256@2x.png': 'graph_canvas_512x512.png',
			'icon_512x512.png': 'graph_canvas_512x512.png',
			'icon_512x512@2x.png': 'graph_canvas_1024x1024.png'
		}

		# Copy icons with correct names
		for iconset_name, source_name in icon_mappings.items():
			source_path = icons_dir / source_name
			if source_path.exists():
				shutil.copy2(source_path, iconset_dir / iconset_name)

		# Convert to ICNS using iconutil
		icns_path = resources_path / "graph_canvas.icns"
		result = subprocess.run(
			['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)],
			capture_output=True,
			text=True)

		if result.returncode == 0:
			print("✅ Created ICNS icon file")
			# Clean up iconset directory
			shutil.rmtree(iconset_dir)
		else:
			print("⚠️  Could not create ICNS file, using PNG icon")
			# Fallback: copy the largest PNG icon
			largest_icon = icons_dir / "graph_canvas_512x512.png"
			if largest_icon.exists():
				shutil.copy2(largest_icon, resources_path / "graph_canvas.icns")

	except Exception as e:
		print(f"⚠️  Could not create ICNS icon: {e}")
		# Copy any available icon as fallback
		if (icons_dir / "graph_canvas.png").exists():
			shutil.copy2(icons_dir / "graph_canvas.png", resources_path / "graph_canvas.icns")


def create_dmg_installer():
	"""Create a DMG installer (optional)"""
	app_name = "Graph Canvas"
	bundle_name = f"{app_name}.app"
	dmg_name = f"{app_name}.dmg"

	root = Path(__file__).resolve().parent.parent
	bundle_path = root / bundle_name
	if not bundle_path.exists():
		print("❌ App bundle not found. Create the app bundle first.")
		return

	try:
		import subprocess

		# Remove existing DMG
		dmg_path = root / dmg_name
		if dmg_path.exists():
			os.remove(dmg_path)

		# Create DMG from the .app bundle in root
		subprocess.run([
			'hdiutil', 'create', '-volname', app_name, '-srcfolder', str(bundle_path), '-ov', '-format', 'UDZO', str(dmg_path)
		], check=True)

		print(f"✅ Created installer: {dmg_name}")

	except subprocess.CalledProcessError:
		print("⚠️  Could not create DMG installer")
	except Exception as e:
		print(f"⚠️  DMG creation failed: {e}")


if __name__ == "__main__":
	print("🏗️  Creating macOS Application Bundle...")
	bundle_name = create_app_bundle()

	print("\n📦 Would you like to create a DMG installer? (y/n): ", end="")
	try:
		response = input().lower().strip()
		if response in ['y', 'yes']:
			create_dmg_installer()
	except (EOFError, KeyboardInterrupt):
		pass

	print("\n🎉 Application bundle creation complete!")
	print(f"🚀 Launch: Double-click {bundle_name}")
	print(f"📱 Install: Drag {bundle_name} to Applications folder")
