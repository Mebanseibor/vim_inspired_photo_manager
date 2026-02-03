import gc

from PIL import Image, ImageTk


class Coordinate:
    def __init__(self, x: int, y: int):
        self.x: int = x
        self.y: int = y


class Holder:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        self.center_x: int = int(self.width / 2)
        self.center_y: int = int(self.height / 2)


class CanvasImage:
    def __init__(self, image: Image.Image, holder: Holder):
        self.image: Image.Image = image
        self.imageTk: ImageTk.PhotoImage = ImageTk.PhotoImage(self.image)
        self.width: int = self.image.width
        self.height: int = self.image.height
        self.holder: Holder = holder

        # zoom
        self.curr_zoom: float = 1.0
        self.zooming_factor: float = 2
        self.zoom_in_limit: float = 2.0

        self.zoom_out_limit: float
        if self.width <= holder.width and self.height <= holder.height:
            self.zoom_out_limit = self.curr_zoom
        else:
            # when width/height is greater, limit zoom out till width/height fills the canvas
            if self.width <= self.height:
                a, b = self.width, holder.width
                bigger_width, smaller_width = max(a, b), min(a, b)
                self.zoom_out_limit = smaller_width / bigger_width
            else:
                a, b = self.height, holder.height
                bigger_height, smaller_height = max(a, b), min(a, b)
                self.zoom_out_limit = smaller_height / bigger_height
                self.zoom_out_limit = smaller_height / bigger_height

        self.zoom_cache: dict[float, ImageTk.PhotoImage] = {
            self.curr_zoom: self.imageTk
        }

    def center_of_tk_image(self) -> Coordinate:
        return Coordinate(int(self.imageTk.width() / 2), int(self.imageTk.height() / 2))

    def zoom_in(self):
        intended_zoom = self.curr_zoom * self.zooming_factor
        if intended_zoom > self.zoom_in_limit:
            self.imageTk = self.zoom_cache.get(
                self.zoom_in_limit,
                self.get_or_create_image_at_scale_factor(self.zoom_in_limit),
            )
            return
        self.imageTk = self.get_or_create_image_at_scale_factor(intended_zoom)

    def zoom_out(self):
        intended_zoom = self.curr_zoom / self.zooming_factor
        if intended_zoom < self.zoom_out_limit:
            self.imageTk = self.zoom_cache.get(
                self.zoom_out_limit,
                self.get_or_create_image_at_scale_factor(self.zoom_out_limit),
            )
            return
        self.imageTk = self.get_or_create_image_at_scale_factor(intended_zoom)

    def set_zoom_to_zoom_out_limit(self):
        self.imageTk = self.get_or_create_image_at_scale_factor(self.zoom_out_limit)

    def set_zoom_to_fit(self):
        self.curr_zoom = 1.0
        self.imageTk = self.get_or_create_image_at_scale_factor(self.curr_zoom)

    def get_or_create_image_at_scale_factor(
        self, scale_factor: float
    ) -> ImageTk.PhotoImage:
        self.curr_zoom = scale_factor
        if self.zoom_cache.get(scale_factor):
            return self.zoom_cache[scale_factor]

        new_width = int(self.image.width * scale_factor)
        new_height = int(self.image.height * scale_factor)
        is_imageTk_bigger_than_canvas_holder: bool = (
            new_height >= self.holder.height or new_width >= self.holder.width
        )
        resampling_mode = (
            Image.Resampling.NEAREST
            if is_imageTk_bigger_than_canvas_holder
            else Image.Resampling.LANCZOS
        )
        new_image = self.image.resize((new_width, new_height), resampling_mode)
        self.zoom_cache[scale_factor] = ImageTk.PhotoImage(new_image)
        gc.collect()
        return self.zoom_cache[scale_factor]
