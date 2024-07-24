from .bot import kdi
from .relay import RelayPlugin

if __name__ == "__main__":
	relay = RelayPlugin()

	kdi.run()
