from PyQt5.sip import wrapper

from app.common.qfluentwidgets import SmoothScrollArea


class SeraphineInterface(SmoothScrollArea):
    def __str__(self):
        methods = [attr for attr in dir(self) if callable(getattr(self, attr))]
        attrs = [f"{k}({type(v).__name__})={v!r}" for k, v in self.__dict__.items() if
                 not isinstance(v, wrapper) and k not in methods]
        return f"{self.__class__.__name__}(\n  {', '.join(attrs)}\n)"
