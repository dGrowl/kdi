from .bot import kdi

from .relay import relay_plugin

if __name__ == "__main__":
	kdi.add_plugin(relay_plugin)
	kdi.run()
