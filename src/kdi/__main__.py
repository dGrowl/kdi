from .bot import kdi

from .relay import relay_plugin
from .teams import teams_plugin

if __name__ == "__main__":
	kdi.add_plugin(relay_plugin)
	kdi.add_plugin(teams_plugin)
	kdi.run()
