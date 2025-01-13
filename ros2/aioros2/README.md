# aioros2
The point of this library is to make working with ROS2/`rclpy` bearable (and possibly even enjoyable). Its syntax is heavily inspired by `python-socketio`.

## Features
- Massive boilerplate reduction
- First-class asyncio compatibility.
- Generators instead of callbacks
- Transparent clients (use the same class as both client and server)

## Installation
This will install `aioros2` in dev mode in the current environment
```
$ cd aioros2
$ pip install -e . --config-settings editable_mode=strict
```

### Feature Tracker
- [ ] Action Server
- [x] Service Server
- [ ] Service Client
- [ ] Action Client
- [x] Topic Publisher
- [x] Topic Subscriber
- [x] Server timer tasks
- [x] Launch files
- [x] Server background tasks
- [x] Parameters
- [ ] Comprehensive error handling

## Limitations
- Param dataclasses must be flat.
- Non-async handlers are not currently supported
- Probably fragile. Next steps are improving validation, error handling, and error messaging
