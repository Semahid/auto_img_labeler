import os
import shutil
import random
from pathlib import Path


class DatasetSplitter:
    """YOLO veri setini train, validation ve test olarak böler"""

    def __init__(self, source_dir, output_dir):
        self.source_dir = source_dir
        self.output_dir = output_dir

    def split_dataset(
        self, train_ratio=70, val_ratio=20, test_ratio=10, save_yaml=True
    ):
        """
        Veri setini belirtilen oranlarda böler

        Args:
            train_ratio (int): Eğitim seti yüzdesi
            val_ratio (int): Doğrulama seti yüzdesi
            test_ratio (int): Test seti yüzdesi
            save_yaml (bool): data.yaml dosyasını oluşturup oluşturmayacağı

        Returns:
            dict: Bölümlendirme sonuçları
        """
        # Toplam oranın 100 olduğunu kontrol et
        assert (
            train_ratio + val_ratio + test_ratio == 100
        ), "Oranların toplamı 100 olmalıdır"

        # Annotations klasörünü bul
        annotations_dir = os.path.join(self.source_dir, "annotations")
        if not os.path.exists(annotations_dir):
            raise FileNotFoundError(
                f"Annotations klasörü bulunamadı: {annotations_dir}"
            )

        # Resim dosyalarını bul
        image_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".JPG",
            ".JPEG",
            ".PNG",
        ]
        image_files = []

        for file in os.listdir(self.source_dir):
            file_path = os.path.join(self.source_dir, file)
            if os.path.isfile(file_path) and any(
                file.lower().endswith(ext) for ext in image_extensions
            ):
                # Annotation dosyasının var olduğunu kontrol et
                img_name = os.path.splitext(file)[0]
                label_path = os.path.join(annotations_dir, f"{img_name}.txt")

                if os.path.exists(label_path):
                    image_files.append(file)

        # Rastgele karıştır
        random.shuffle(image_files)

        # Bölümleme indekslerini hesapla
        train_end = int(len(image_files) * train_ratio / 100)
        val_end = train_end + int(len(image_files) * val_ratio / 100)

        # Veri setlerini oluştur
        train_files = image_files[:train_end]
        val_files = image_files[train_end:val_end]
        test_files = image_files[val_end:]

        # Hedef klasörleri oluştur
        dataset_dir = os.path.join(self.output_dir, "dataset")
        train_dir = os.path.join(dataset_dir, "train")
        val_dir = os.path.join(dataset_dir, "val")
        test_dir = os.path.join(dataset_dir, "test")

        train_img_dir = os.path.join(train_dir, "images")
        train_label_dir = os.path.join(train_dir, "labels")

        val_img_dir = os.path.join(val_dir, "images")
        val_label_dir = os.path.join(val_dir, "labels")

        test_img_dir = os.path.join(test_dir, "images")
        test_label_dir = os.path.join(test_dir, "labels")

        # Klasörleri temizle ve oluştur
        for directory in [
            train_img_dir,
            train_label_dir,
            val_img_dir,
            val_label_dir,
            test_img_dir,
            test_label_dir,
        ]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            os.makedirs(directory)

        # Dosyaları kopyala
        self._copy_files(train_files, train_img_dir, train_label_dir)
        self._copy_files(val_files, val_img_dir, val_label_dir)
        self._copy_files(test_files, test_img_dir, test_label_dir)

        # YAML dosyasını oluştur
        if save_yaml:
            yaml_path = self._create_yaml_file(dataset_dir)
        else:
            yaml_path = None

        # Sonuçları döndür
        return {
            "train_count": len(train_files),
            "val_count": len(val_files),
            "test_count": len(test_files),
            "total_count": len(image_files),
            "dataset_dir": dataset_dir,
            "yaml_path": yaml_path,
        }

    def _copy_files(self, files, img_dir, label_dir):
        """Resim ve etiket dosyalarını hedef klasörlere kopyalar"""
        for file in files:
            # Resim dosyasını kopyala
            src_img = os.path.join(self.source_dir, file)
            dst_img = os.path.join(img_dir, file)
            shutil.copy2(src_img, dst_img)

            # Etiket dosyasını kopyala
            img_name = os.path.splitext(file)[0]
            src_label = os.path.join(self.source_dir, "annotations", f"{img_name}.txt")
            dst_label = os.path.join(label_dir, f"{img_name}.txt")

            if os.path.exists(src_label):
                shutil.copy2(src_label, dst_label)

    def create_yaml_file(self, dataset_dir=None):
        """data.yaml dosyasını oluşturur"""
        if dataset_dir is None:
            dataset_dir = os.path.join(self.output_dir, "dataset")

        # Sınıf isimlerini al
        classes_file = os.path.join(self.source_dir, "annotations", "classes.json")

        import json

        if os.path.exists(classes_file):
            with open(classes_file, "r") as f:
                classes = json.load(f)
        else:
            # classes.txt dosyasını da kontrol et
            classes_txt = os.path.join(self.source_dir, "annotations", "classes.txt")
            if os.path.exists(classes_txt):
                with open(classes_txt, "r") as f:
                    classes = [line.strip() for line in f if line.strip()]
            else:
                classes = ["default"]  # Varsayılan sınıf

        # data.yaml dosyasını oluştur
        yaml_path = os.path.join(dataset_dir, "data.yaml")

        # Path nesneleri oluştur (göreceli yollar için)
        yaml_dir = Path(yaml_path).parent
        train_path = Path(os.path.join(dataset_dir, "train"))
        val_path = Path(os.path.join(dataset_dir, "val"))
        test_path = Path(os.path.join(dataset_dir, "test"))

        # Göreceli yolları hesapla
        train_rel = os.path.relpath(train_path, yaml_dir)
        val_rel = os.path.relpath(val_path, yaml_dir)
        test_rel = os.path.relpath(test_path, yaml_dir)

        # YAML içeriğini oluştur
        yaml_content = f"""# YOLOv8 Configuration
# Train/val/test sets as 1) dir: path/to/imgs, 2) file: path/to/imgs.txt, or 3) list: [path/to/imgs1, path/to/imgs2, ..]
path: {os.path.abspath(dataset_dir)}  # dataset root dir
train: {train_rel}/images  # train images
val: {val_rel}/images  # val images
test: {test_rel}/images  # test images

# Classes
names:
{chr(10).join([f'  {i}: {c}' for i, c in enumerate(classes)])}
"""

        # YAML dosyasını yaz
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        return yaml_path

    def _create_yaml_file(self, dataset_dir):
        """create_yaml_file metodunu split_dataset içinden çağırır"""
        return self.create_yaml_file(dataset_dir)
