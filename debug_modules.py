import sys
import os
sys.path.append(os.getcwd())

try:
    from backend.routers import parts_gnc
    print("Import parts_gnc successful")
    from backend.services import orders
    print("Import orders successful")
    from backend import models
    print("Import models successful")
except Exception as e:
    import traceback
    traceback.print_exc()
