import logging
import time
import subprocess
import os
import stat

from django.conf import settings

from sorl.thumbnail.base import ThumbnailBackend


logger = logging.getLogger('optisorl')


class OptimizingThumbnailBackend(ThumbnailBackend):

    def _create_thumbnail(self, source_image, geometry_string, options, thumbnail):
        """override so we have an opportunity to first optimize the
        resulting thumbnail before it gets saved."""
        super(OptimizingThumbnailBackend, self)._create_thumbnail(
            source_image,
            geometry_string, options,
            thumbnail
        )
        image_path = os.path.join(settings.MEDIA_ROOT, thumbnail.name)
        if os.path.isfile(image_path):
            if image_path.lower().endswith('.png'):
                return self.optimize_png(image_path)
            elif image_path.lower().endswith('.gif'):
                return self.optimize_gif(image_path)
            elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                return self.optimize_jpg(image_path)

    def optimize_png(self, path):
        binary_location = getattr(
            settings,
            'OPTISORL_PNG_LOCATION',
            'pngquant'
        )
        if not binary_location:
            # it's probably been deliberately disabled
            return
        tmp_path = path.lower().replace('.png', '.tmp.png')
        size_before = os.stat(path).st_size
        command = [
            binary_location,
            '-o', tmp_path,
            '--skip-if-larger',
            '--quality=85',
            path,
        ]
        time_before = time.time()
        out, err = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        time_after = time.time()
        # Because we use --skip-if-larger, when you resize an already
        # small PNG the resulting one might not be any smaller so you
        # can't guarantee that the new file was created.
        if not os.path.isfile(tmp_path):
            return
        os.rename(tmp_path, path)
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR | stat.S_IWGRP)
        size_after = os.stat(path).st_size
        logger.info(
            'Reduced %s from %d to %d (took %.4fs)' % (
                os.path.basename(path),
                size_before,
                size_after,
                time_after - time_before
            )
        )
        return True  # it worked

    def optimize_gif(self, path):
        binary_location = getattr(
            settings,
            'OPTISORL_GIF_LOCATION',
            'gifsicle'
        )
        if not binary_location:
            # it's probably been deliberately disabled
            return
        tmp_path = path.lower().replace('.gif', '.tmp.gif')
        size_before = os.stat(path).st_size
        command = [
            binary_location,
            '-O3', path,
            '-o', tmp_path,
        ]
        time_before = time.time()
        out, err = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        time_after = time.time()
        if not os.path.isfile(tmp_path):
            return
        os.rename(tmp_path, path)
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR | stat.S_IWGRP)
        size_after = os.stat(path).st_size
        logger.info(
            'Reduced %s from %d to %d (took %.4fs)' % (
                os.path.basename(path),
                size_before,
                size_after,
                time_after - time_before
            )
        )
        return True  # it worked

    def optimize_jpg(self, path):
        binary_location = getattr(
            settings,
            'OPTISORL_JPEG_LOCATION',
            'jpegoptim'
        )
        if not binary_location:
            # it's probably been deliberately disabled
            return
        tmp_path = path.lower().replace('.jpg', '.tmp.jpg')
        size_before = os.stat(path).st_size
        command = [
            binary_location,
            '--max=85',
            '--strip-all', path,
        ]
        time_before = time.time()
        out, err = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        time_after = time.time()
        if not os.path.isfile(tmp_path):
            return
        os.rename(tmp_path, path)
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR | stat.S_IWGRP)
        size_after = os.stat(path).st_size
        logger.info(
            'Reduced %s from %d to %d (took %.4fs)' % (
                os.path.basename(path),
                size_before,
                size_after,
                time_after - time_before
            )
        )
        return True  # it worked
