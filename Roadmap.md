# Features Roadmap

## All Services Stuff

[ ] Build a Services Manager screen to view the status of all services
[X] Build a run_worker bridge function in BaseService so that services can run workers

## App SDK

[ ] Create test/dummy app to test the SDK and loader service
[ ] Make app create a /home/user/term-desktop/apps folder for local dev
[X] Build a way for 'apps' to be entire packages instead of only .py files
[X] Build validation for existence of required abstract methods in AppLoader
[X] Implement `BROKEN` and `MISSING_METHODS` class vars in `TDEApp` base class
[X] Build a base widget for the "TDEMainWidget" to provide some built-in functionality.
[X] Create an 'initialized' message for the ProcessManager to trigger on the app's main widget.
[X] Implement the window styles dictionary from Textual-window library
[X] Make the ProcessManager set the `process_id` attribute on the main widget of the app

## Window Service

[X] Implement the `get_window_by_process_id` method in WindowService

## App Selector / File Associator

[ ] Build file association service
[X] Build app selector window

## User Settings

[ ] Build user settings app
[ ] Implement SQLite for storing user settings

## Start Menu

[ ] Implement fuzzy finder in start menu
[ ] Add icons to start menu
[ ] Create different sections in start menu

## Desktop

[ ] Create boot screen
[ ] Build desktop/theme customization app
[ ] Desktop icons

## File Explorer

[ ] Build way to change root directory
[ ] Add file search functionality
[ ] Add file preview functionality
[ ] Add file operations (copy, move, delete, rename)
[X] Build file explorer info box
[ ] Implement Textual-FSpicker for something (not sure yet... but something, surely.)

## Apps

[ ] Build TaskBuddy app
[ ] Add TipTop as the built-in resource monitor
