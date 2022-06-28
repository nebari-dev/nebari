# Using Visual Studio (VS) Code

How to use VS Code as your development environment.

VS Code can be used as an IDE (integrated development environment) which 
provides helpful tooling (including debuging) to assist developers in writing 
code. It also has many other functions which non-developers may also find 
useful such a text editing and markdown rendering. 

## Getting started

VS Code comes built-in with every installation of Nebari. To start, log in
to Nebari and spin up a JupyterLab instance. 

Next, bring up the `New Launcher` window by clicking the `+` in the top left of
the screen. Now click on the VS Code logo on the Launcher window. 

![JupyterLab Launcher window with VS Code](/img/vscode_launcher.png)

You will now have been redirected to a new web browser page showing the VS 
Code platform. If you're starting VS Code for the first time, you'll see a 
Welcome Page with some helpful links and tips. 

Feel free to explore! 

![VS code Welcome screen](/img/vscode_welcome.png)

## VS Code components

On the far left, you'll see the `Activity Bar` in black. Also on the left is 
the `Explorer`. As you click on the items in the `Activity Bar`, the `Explorer` 
items will update. 

Let's review some of the most useful features. 

### The Activity Bar components

The `Activity Bar` is where you'll go to switch between the main tools 
availiable in VS Code. Below is a brief overview of the icons on the 
`Activity Bar` (adding extensions may add additional icons your menu). 

| Icon      | Name  |  Description |
| ----------- | ----------- | ---------- |
| ![VS code hamburger button](/img/vscode_hamburger.png) | File Menu | Like every other file menu - create files, run files, edit preferences... | 
| ![VS code files button](/img/vscode_files.png) | File Explorer | View list of files, navigate folder structures |
| ![VS code search button](/img/vscode_search.png) | Search | Search for words in the contents of files |
| ![VS code source control button](/img/vscode_source_control.png) | Source Control | Souce Control Management (SCM) features (e.g. git) |
| ![VS code debug button](/img/vscode_debug.png) | Debug | Run code using the debugger |
| ![VS code extensions button](/img/vscode_extensions.png) | Extensions | Add plugins to extend VS Code functionality |

## File editing

Now that we have that out of the way, let's explore! 

We'll start by clicking on the `File Explorer` icon. The `Explorer` sidebar now 
is updated with our filesystem. In our case, this is our Nebari user root 
directory. 

One of the first things you'll notice here is that there are a lot of files 
starting with the `.` character. This is particularly handy because JupyterLab 
hides these files in it's Explorer view. 

Let's click on a file we all have, `.bashrc`. This file was created by Nebari 
for us.

![VS code bashrc file](/img/vscode_bashrc.png)

We now have an `Editor` window in which we can modify the file. The default 
VS Code preferences include an auto-save feature which will continually save 
the files as soon as you stop typing edits. 

## Adding extensions

Using the `Activity Bar`, navigate to the `Extensions`. The `Explorer` sidebar 
now shows lists of Extensions, grouped by those installed by your admin, those 
installed by you, and a list of "Popular" extensions you may want to try. 
Through this interface we can also search the Marketplace for a particular 
extension. 

![VS code extensions list](/img/vscode_extensions_list.png)

The Python extension is at the top of the list in our example (rightly so!), 
but if you don't see it here, you can search for it. 

If you click on the Python extension, you'll see additional information about 
this extension in the main window. This extension provides some extra tooling
around Python. It will allow us to select a Python environment and run and 
debug code right inside of VS Code. Go ahead and click `Install`. It should 
only take a few seconds to install. 

Now let's run some code!

## Running Python code


