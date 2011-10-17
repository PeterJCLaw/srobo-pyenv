import pykoki, threading, time
from collections import namedtuple
from pykoki import CameraParams, Point2Df, Point2Di

# TODO: These numbers require calibration
camera_focal_length = {
    (640,480): (571, 571),
    (800,600): (571, 571),
    (1280,1024): (571, 571)
}

MARKER_ARENA, MARKER_ROBOT, MARKER_TOKEN, \
MARKER_BUCKET_SIDE, MARKER_BUCKET_END = range(0,5)

marker_offsets = {
    MARKER_ARENA: 0,
    MARKER_ROBOT: 28,
    MARKER_TOKEN: 32,
    MARKER_BUCKET_SIDE: 72,
    MARKER_BUCKET_END: 76
}

marker_sizes = {
    MARKER_ARENA: 0.25 * (10.0/12),
    MARKER_ROBOT: 0.1 * (10.0/12),
    MARKER_TOKEN: 0.1 * (10.0/12),
    MARKER_BUCKET_SIDE: 0.1 * (10.0/12),
    MARKER_BUCKET_END: 0.1 * (10.0/12)
}

MarkerInfo = namedtuple( "MarkerInfo", "code marker_type offset size" )
ImageCoord = namedtuple( "ImageCoord", "x y" )
WorldCoord = namedtuple( "WorldCoord", "x y z" )
PolarCoord = namedtuple( "PolarCoord", "length rot_x rot_y" )
Orientation = namedtuple( "Orientation", "rot_x rot_y rot_z" )
Point = namedtuple( "Point", "image world polar" )

def create_marker_lut(offset):
    lut = {}
    for genre, num in [ ( MARKER_ARENA, 28 ),
                        ( MARKER_ROBOT, 4 ),
                        ( MARKER_TOKEN, 40 ),
                        ( MARKER_BUCKET_SIDE, 4 ),
                        ( MARKER_BUCKET_END, 4 ) ]:

        for n in range(0,num):
            code = code = offset + marker_offsets[genre] + n
            m = MarkerInfo( code = code,
                            marker_type = genre,
                            offset = n,
                            size = marker_sizes[genre] )
            lut[code] = m
    return lut

marker_luts = { "dev": create_marker_lut(0),
                "comp": create_marker_lut(100) }

MarkerBase = namedtuple( "Marker", "info timestamp res vertices centre orientation" ) 
class Marker(MarkerBase):
    def __init__( self, *a, **kwd ):
        MarkerBase.__init__(self, *a, **kwd)

        # Aliases
        self.dist = self.centre.polar.length
        self.rot_y = self.centre.polar.rot_y

class Vision(object):
    def __init__(self, camdev, lib):
        self.koki = pykoki.PyKoki(lib)
        self._camdev = camdev
        self.fd = self.koki.v4l_open_cam(self._camdev)

        if self.fd < 0:
            raise Exception("Couldn't open camera: %s" % ctypes.get_errno() )

        # Lock for the use of the vision
        self.lock = threading.Lock()
        self.lock.acquire()

        self._res = None
        self._buffers = None
        self._streaming = False

        # Default to 800x600        
        self._set_res( (800,600) )
        self._start()
        self.lock.release()

    def _set_res(self, res):
        "Set the resolution of the camera if different to what we were"
        if res == self._res:
            "Resolution already the requested one"
            return
        print "Res change"

        was_streaming = self._streaming
        if was_streaming:
            self._stop()

        # The camera goes into a strop if we don't close and open again
        self.koki.v4l_close_cam(self.fd)
        self.fd = self.koki.v4l_open_cam(self._camdev)

        fmt = self.koki.v4l_create_YUYV_format( res[0], res[1] )
        self.koki.v4l_set_format(self.fd, fmt)

        fmt = self.koki.v4l_get_format(self.fd)
        width = fmt.fmt.pix.width
        height = fmt.fmt.pix.height

        if width != res[0] or height != res[1]:
            print width, height, res
            raise ValueError( "Unsupported image resolution" )
        self._res = (width, height)

        if was_streaming:
            self._start()

    def _stop(self):
        self.koki.v4l_stop_stream(self.fd)
        self.koki.v4l_free_buffers(self._buffers, 1)
        self._buffers = None
        self._streaming = False

    def _start(self):
        self._buffers = self.koki.v4l_prepare_buffers(self.fd, pykoki.c_int(1))
        self.koki.v4l_start_stream(self.fd)
        self._streaming = True

    def _width_from_code(self, code):
        return 0.1 * (10.0/12.0)

    def see(self, mode, res):
        self.lock.acquire()
        self._set_res(res)

        acq_time = time.time()
        frame = self.koki.v4l_get_frame_array( self.fd, self._buffers )
        img = self.koki.v4l_YUYV_frame_to_RGB_image( frame, self._res[0], self._res[1] )
        # Now that we're dealing with a copy of the image, release the camera lock
        self.lock.release()

        print "acq time", time.time() - acq_time
        t1 = time.time()
        params = CameraParams( Point2Df( self._res[0]/2,
                                         self._res[1]/2 ),
                               Point2Df( *camera_focal_length[ self._res ] ),
                               Point2Di( *self._res ) )

        markers = self.koki.find_markers_fp( img, self._width_from_code, params )

        print "proc time:", time.time() - t1

        srmarkers = []
        for m in markers:
            info = marker_luts[mode][int(m.code)]

            vertices = []
            for v in m.vertices:
                vertices.append( Point( image = ImageCoord( x = v.image.x,
                                                            y = v.image.y ),
                                        world = WorldCoord( x = v.world.x,
                                                            y = v.world.y,
                                                            z = v.world.z ),
                                        # libkoki does not yet provide these coords
                                        polar = PolarCoord( 0,0,0 ) ) )

            centre = Point( image = ImageCoord( x = m.centre.image.x,
                                                y = m.centre.image.y ),
                            world = WorldCoord( x = m.centre.world.x,
                                                y = m.centre.world.y,
                                                z = m.centre.world.z ),
                            polar = PolarCoord( length = m.distance,
                                                rot_x = m.bearing.x,
                                                rot_y = m.bearing.y ) )

            orientation = Orientation( rot_x = m.rotation.x,
                                       rot_y = m.rotation.y,
                                       rot_z = m.rotation.z )

            marker = Marker( info = info,
                             timestamp = acq_time,
                             res = res,
                             vertices = vertices,
                             centre = centre,
                             orientation = orientation )
            srmarkers.append(marker)

        self.koki.image_free(img)
        return srmarkers
