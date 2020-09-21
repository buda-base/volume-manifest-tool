import io
import json
import os
import sys
from pathlib import Path, PurePath

import aiofiles

from v_m_b.ImageRepository.ImageRepositoryBase import ImageRepositoryBase
from v_m_b.VolumeInfo.VolInfo import VolInfo
from v_m_b.ImageRepository.ImageGroupResolver import ImageGroupResolver
import v_m_b.manifestCommons as Common


class FSImageRepository(ImageRepositoryBase):

    def manifest_exists(self, work_Rid: str, image_group_id: str) -> bool:
        """
        tests for a well known item in the repository
        :param work_Rid:
        :param image_group_id:
        :return:
        """
        return Path(self._IGResolver.full_path(work_Rid, image_group_id), 'dimensions.json').exists()

    def generateManifest(self, work_Rid: str, vol_info: VolInfo) -> []:
        if self.manifest_exists(work_Rid, vol_info.imageGroupID):
            self.repo_log.info(f"manifest exists for work{work_Rid} image group {vol_info.imageGroupID}")
        import asyncio
        full_path: Path = self._IGResolver.full_path(work_Rid, vol_info.imageGroupID)
        manifest = asyncio.run(generateManifest_a(full_path, vol_info.image_list))
        # generateManifest_s(full_path, vol_info.image_list)
        return manifest

    def __init__(self, bom_key: str, source_root: str, images_name: str):
        """
        Creation.
        :param source_root: parent of all works in the repository. Existing directory name
        :param images_name: subfolder of the work which contains the image group folders
        """
        super(FSImageRepository, self).__init__(bom_key)
        self._container = source_root
        self._image_folder_name = images_name
        self._IGResolver = ImageGroupResolver(source_root, images_name)

    def getImageNames(self, work_rid: str, image_group: str, bom_name: str) -> []:
        """
        File system implementation
        :param work_rid: locator
        :param image_group: locator
        :param bom_name: file name of BOM
        :return: list of images in an image group, either from the BOM or by listing all the non json files in a folder
        """

        bom_home = self._IGResolver.full_path(work_rid, image_group)
        bom_path = Path(bom_home, bom_name)

        image_list: [] = []

        # try reading the bom first
        if bom_path.exists():
            with open(bom_path, "rb") as f:
                json_body = json.loads(f.read())
                image_list = [x[Common.VMT_BUDABOM_JSON_KEY] for x in json_body]
        else:
            if bom_home.exists():
                image_list = [f for f in os.listdir(str(bom_home)) if os.path.isfile(Path(bom_home, f))
                              and not str(f).lower().endswith('json')]
        return image_list

    def uploadManifest(self, work_rid: str, image_group: str, bom_name: str, manifest_zip: bytes):
        """
        FS implemenation
        :param work_rid:
        :param image_group:
        :param bom_name: output object name
        :param manifest_zip:
        :return:
        """
        bom_path = Path(self._IGResolver.full_path(work_rid, image_group), bom_name)
        with open(bom_path, "wb") as upl:
            upl.write(manifest_zip)

    def getPathfromLocators(self, work_Rid: str, image_group_id: str) -> str:
        """
        :param work_Rid: Work resource id
        :param image_group_id: image group - gets transformed
        :returns:  the s3 prefix (~folder) in which the volume will be present.
        gives the s3 prefix (~folder) in which the volume will be present.
        inpire from https://github.com/buda-base/buda-iiif-presentation/blob/master/src/main/java/
        io/bdrc/iiif/presentation/ImageInfoListService.java#L73
        Example:
           - workRID=W22084, imageGroupID=I0886
           - result = "Works/60/W22084/images/W22084-0886/
        where:
           - 60 is the first two characters of the md5 of the string W22084
           - 0886 is:
              * the image group ID without the initial "I" if the image group ID is in the form I\\d\\d\\d\\d
              * or else the full image group ID (incuding the "I")
        """
        suffix = self.getImageGroup(image_group_id)
        return f"{self._container}/{work_Rid}/images/{work_Rid}-{suffix}"


# downloading region
async def generateManifest_a(ig_container: PurePath, image_list: []) -> []:
    """
    this actually generates the manifest. See example in the repo. The example corresponds to W22084, image group I0886.
    :param ig_container: path of parent of image group
    :param image_list: list of image names
    :returns: list of  internal data for each file in image_list
    """

    res: [] = []

    image_file_name: str
    for image_file_name in image_list:
        image_path: Path = Path(ig_container, image_file_name)
        imgdata = {"filename": image_file_name}
        res.append(imgdata)
        # extracted from fillData
        async with aiofiles.open(image_path, "rb") as image_file:
            image_buffer: bytes = await image_file.read()
            bio: io.BytesIO = io.BytesIO(image_buffer)
            Common.fillDataWithBlobImage(bio, imgdata)
    return res


def generateManifest_s(ig_container: PurePath, image_list: []) -> []:
    """
    this actually generates the manifest. See example in the repo. The example corresponds to W22084, image group I0886.
    :param ig_container: path of parent of image group
    :param image_list: list of image names
    :returns: list of  internal data for each file in image_list
    """

    res = []

    image_file_name: str
    for image_file_name in image_list:
        image_path: Path = Path(ig_container, image_file_name)
        imgdata = {"filename": image_file_name}
        res.append(imgdata)
        # extracted from fillData
        with open(str(image_path), "rb") as image_file:
            image_buffer = image_file.read()
            # image_buffer = io.BytesIO(image_file.read())
            try:
                fillDataWithBlobImage(io.BytesIO(image_buffer), imgdata)
            except Exception as eek:
                exc = sys.exc_info()
                print(eek, exc[0])
        # asyncio.run(fillData(image_path, imgdata))
    return res
# end region