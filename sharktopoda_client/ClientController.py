from abc import ABC, abstractmethod
from typing import Awaitable, List, Optional
from uuid import UUID
from os import PathLike

from sharktopoda_client.model.Video import Video
from sharktopoda_client.model.FrameCapture import FrameCapture


class ClientController(ABC):
    """
    This interface should be implemented for applications that use UDP comms
    for video control via the vcr4j-sharktopoda module. Your controller implementation
    can choose to support multiple video windows, with each video having an
    associated UUID. If you choose to do this, the videoUuid parameter should
    be used to lookup the video/window to direct the commands to.
    """
    
    @abstractmethod
    def open(self, videoUuid: UUID, url: str) -> bool:
        """
        Opens a video and focuses its window/stage. If the video with that UUID
        already exists then just focus its window/stage.

        :param videoUuid: Key to associate with video
        :type videoUuid: UUID
        :param url: The URL (either http or file) of the video to be opened.
        :type url: str
        :return: true if successful, false if unable to open the video
        :rtype: bool
        """
        raise NotImplementedError()
    
    @abstractmethod
    def close(self, videoUuid: UUID) -> bool:
        """
        Closes a video window if it exists.

        :param videoUuid:
        :type videoUuid: UUID
        :return: true if successful, false if it failed or the video does not exist
        :rtype: bool
        """
        raise NotImplementedError()
    
    @abstractmethod
    def show(self, videoUuid: UUID) -> bool:
        """
        Focuses an already open video/window and brings it to the foreground.

        :param videoUuid: 
        :type videoUuid: UUID
        :return: true if successful, false if it failed or the video does not exist
        :rtype: bool
        """
        raise NotImplementedError()

    @abstractmethod
    def requestVideoInfo() -> Optional[Video]:
        """
        
        :return: Returns a Video object representing the currently focused video/window.
        The optional is empty if no window is currently opened.
        :rtype: Optional[Video]
        """
        raise NotImplementedError()
    
    @abstractmethod
    def requestAllVideoInfos() -> List[Video]:
        """

        :return: A list of all currently open videos
        :rtype: List[Video]
        """
        raise NotImplementedError()
    
    @abstractmethod
    def play(self, videoUuid: UUID) -> bool:
        """
        Sets the playback rate of the current window. 0 is stopped. 1 is normal
        playback rate. Negative values are reverse shuttling. Refer to your media API to
        see what the max and min allowed are. Note some codecs and APIs may not
        support reverse playback.

        :param videoUuid:
        :type videoUuid: UUID
        :return:
        :rtype: bool
        """
        raise NotImplementedError()
    
    @abstractmethod
    def pause(self, videoUuid: UUID) -> bool:
        """
        Stops playback but keeps the window open. Essentially the same as calling
        `play(uuid, 0)`

        :param videoUuid:
        :type videoUuid: UUID
        :return:
        :rtype: bool
        """
        raise NotImplementedError()

    @abstractmethod
    def requestRate(self, videoUuid: UUID) -> Optional[float]:
        """
        
        :param videoUuid:
        :type videoUuid: UUID
        :return: The rate that the video is playing. This is used to infer status.
        0 is stopped. 1 is playing. Other +/- values indicate the shuttle rate
        :rtype: Optional[float]
        """
        raise NotImplementedError()
    
    @abstractmethod
    def requestElapsedTime(self, videoUuid: UUID) -> Optional[int]:
        """

        :param videoUuid: 
        :type videoUuid: UUID
        :return: The current elapsed time into the video
        :rtype: Optional[int]
        """
        raise NotImplementedError()
    
    @abstractmethod
    def seekElapsedTime(self, videoUuid: UUID, elapsedTime: int) -> bool:
        """
        Jumps to this point in the video

        :param videoUuid:
        :type videoUuid: UUID
        :param elapsedTime:
        :type elapsedTime: int
        :return:
        :rtype: bool
        """
        raise NotImplementedError()
    
    @abstractmethod
    def frameAdvance(self, videoUuid: UUID) -> bool:
        """
        Advance the video a single frame (or some approximating of a very small
        jump forward)

        :param videoUuid:
        :type videoUuid: UUID
        :return:
        :rtype: bool
        """
        raise NotImplementedError()
    
    @abstractmethod
    def frameCapture(self, videoUuid: UUID, saveLocation: PathLike) -> Awaitable[FrameCapture]:
        """
        Grab a frame from the current location of the specified video and write it
        to disk to __saveLocation__.
        Important: Be careful with threading when doing a framecapture. As much
        as possible, IO should be done off of the UI thread.

        :param videoUuid:
        :type videoUuid: UUID
        :param: saveLocation:
        :type saveLocation: PathLike
        :return: A future that completes after the image has been written to disk.
        The future should be complete exceptionally if the image can't be captured
        or written to disk.
        :rtype: Awaitable[FrameCapture]
        """
        raise NotImplementedError()
