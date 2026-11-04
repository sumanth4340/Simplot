# N2 lifecycle probe (INSIDE Isaac Sim): when do rtx_sensor_*
# products exist? Check stopped -> played -> stopped.
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from pxr import UsdRender

st = omni.usd.get_context().get_stage()


def prods(tag):
    ps = sorted(str(p.GetPath()) for p in st.Traverse()
                if p.IsA(UsdRender.Product))
    print(tag, ps)


prods("STOPPED-1")
app_utils.play()
await app_utils.update_app_async(steps=10)
prods("PLAYING")
await app_utils.update_app_async(steps=10)
prods("PLAYING-2")
app_utils.stop()
await app_utils.update_app_async(steps=2)
prods("STOPPED-2")
print("LIFE done")
