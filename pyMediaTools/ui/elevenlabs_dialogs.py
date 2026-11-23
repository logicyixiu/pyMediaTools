from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSlider, QGroupBox, QSizePolicy, 
                               QCheckBox, QTabWidget, QScrollArea, QFrame,
                               QDialog, QDialogButtonBox, QGridLayout, QWidget,
                               QLineEdit, QPushButton, QMessageBox, QFileDialog,
                               QInputDialog, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .styles import apply_common_style
from .elevenlabs_widgets import SubtitlePreviewLabel
from .elevenlabs_style_panel import SubtitleStylePanel
from ..core.elevenlabs import (LibrarySearchWorker, LibraryAddWorker)

class VoiceSettingsDialog(QDialog):
    """语音设定对话框"""
    def __init__(self, parent=None, model_features=None, model_info=None, available_languages=None):
        super().__init__(parent)
        self.setWindowTitle("语音设定")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.stability = 50
        self.similarity = 75
        self.style = 0
        self.speed = 100
        self.speaker_boost = True
        
        self.model_features = model_features or {
            'can_use_style': True,
            'can_use_speaker_boost': True,
        }
        self.model_info = model_info or {}
        self.available_languages = available_languages or []
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("调整语音生成参数")
        title_font = title_label.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Stability
        stability_label = QLabel("稳定性:")
        self.slider_stability = QSlider(Qt.Horizontal)
        self.slider_stability.setRange(0, 100)
        self.slider_stability.setValue(self.stability)
        self.lbl_stability_value = QLabel(f"{self.stability}%")
        self.slider_stability.valueChanged.connect(lambda val: self.lbl_stability_value.setText(f"{val}%"))
        grid_layout.addWidget(stability_label, 0, 0)
        grid_layout.addWidget(self.slider_stability, 0, 1)
        grid_layout.addWidget(self.lbl_stability_value, 0, 2)
        
        # Similarity
        similarity_label = QLabel("相似度提升:")
        self.slider_similarity = QSlider(Qt.Horizontal)
        self.slider_similarity.setRange(0, 100)
        self.slider_similarity.setValue(self.similarity)
        self.lbl_similarity_value = QLabel(f"{self.similarity}%")
        self.slider_similarity.valueChanged.connect(lambda val: self.lbl_similarity_value.setText(f"{val}%"))
        grid_layout.addWidget(similarity_label, 1, 0)
        grid_layout.addWidget(self.slider_similarity, 1, 1)
        grid_layout.addWidget(self.lbl_similarity_value, 1, 2)
        
        # Style
        style_label = QLabel("风格:")
        self.slider_style = QSlider(Qt.Horizontal)
        self.slider_style.setRange(0, 100)
        self.slider_style.setValue(self.style)
        self.lbl_style_value = QLabel(f"{self.style}%")
        self.slider_style.valueChanged.connect(lambda val: self.lbl_style_value.setText(f"{val}%"))
        
        can_use_style = self.model_features.get('can_use_style', True)
        self.slider_style.setEnabled(can_use_style)
        style_label.setEnabled(can_use_style)
        self.lbl_style_value.setEnabled(can_use_style)
        
        grid_layout.addWidget(style_label, 2, 0)
        grid_layout.addWidget(self.slider_style, 2, 1)
        grid_layout.addWidget(self.lbl_style_value, 2, 2)
        
        # Speed
        speed_label = QLabel("速度:")
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(70, 120)
        self.slider_speed.setValue(self.speed)
        self.lbl_speed_value = QLabel(f"{self.speed/100:.2f}")
        self.slider_speed.valueChanged.connect(lambda val: self.lbl_speed_value.setText(f"{val/100:.2f}"))
        grid_layout.addWidget(speed_label, 3, 0)
        grid_layout.addWidget(self.slider_speed, 3, 1)
        grid_layout.addWidget(self.lbl_speed_value, 3, 2)
        
        layout.addLayout(grid_layout)
        
        speaker_lang_layout = QHBoxLayout()
        self.chk_speaker_boost = QCheckBox("扬声器增强")
        self.chk_speaker_boost.setChecked(self.speaker_boost)
        can_use_speaker_boost = self.model_features.get('can_use_speaker_boost', True)
        self.chk_speaker_boost.setEnabled(can_use_speaker_boost)
        
        speaker_lang_layout.addWidget(self.chk_speaker_boost)
        speaker_lang_layout.addStretch()
        
        language_label = QLabel("语言:")
        self.combo_language = QComboBox()
        self.combo_language.addItem("自动检测", None)
        if self.available_languages:
            for name, code in self.available_languages:
                self.combo_language.addItem(name, code)
        else:
            from ..core.elevenlabs import LANGUAGE_CODES
            for code, name in LANGUAGE_CODES.items():
                self.combo_language.addItem(name, code)

        langs = self.model_info.get('languages', [])
        if langs:
            supported_ids = set()
            for lang in langs:
                lang_id = lang.get('language_id') if isinstance(lang, dict) else lang
                supported_ids.add(lang_id)
            for i in range(self.combo_language.count()-1, -1, -1):
                data = self.combo_language.itemData(i)
                if data is None: continue
                if data not in supported_ids:
                    self.combo_language.removeItem(i)
        
        speaker_lang_layout.addWidget(language_label)
        speaker_lang_layout.addWidget(self.combo_language, 1)
        layout.addLayout(speaker_lang_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_settings(self):
        return {
            'stability': self.slider_stability.value() / 100.0,
            'similarity_boost': self.slider_similarity.value() / 100.0,
            'style': self.slider_style.value() / 100.0,
            'use_speaker_boost': self.chk_speaker_boost.isChecked(),
            'speed': self.slider_speed.value() / 100.0,
            'language_code': self.combo_language.currentData()
        }
    
    def set_settings(self, settings):
        if 'stability' in settings:
            val = int(settings['stability'] * 100)
            self.slider_stability.setValue(val)
            self.stability = val
        if 'similarity_boost' in settings:
            val = int(settings['similarity_boost'] * 100)
            self.slider_similarity.setValue(val)
            self.similarity = val
        if 'style' in settings:
            val = int(settings['style'] * 100)
            self.slider_style.setValue(val)
            self.style = val
        if 'speed' in settings:
            val = int(settings['speed'] * 100)
            self.slider_speed.setValue(val)
            self.speed = val
        if 'use_speaker_boost' in settings:
            self.chk_speaker_boost.setChecked(settings['use_speaker_boost'])
            self.speaker_boost = settings['use_speaker_boost']
        if 'language_code' in settings:
            code = settings['language_code']
            if code is None:
                idx = self.combo_language.findData(None)
                if idx >= 0: self.combo_language.setCurrentIndex(idx)
            else:
                idx = self.combo_language.findData(code)
                if idx >= 0: self.combo_language.setCurrentIndex(idx)

class SubtitleSettingsDialog(QDialog):
    """字幕设置对话框 - 整合 Groq 配置、视频分段设置和 XML 样式设置"""
    def __init__(self, parent=None, xml_styles=None, video_settings=None, groq_settings=None):
        super().__init__(parent)
        self.setWindowTitle("字幕设置")
        self.setModal(True)
        self.setMinimumSize(600, 600)
        
        self.parent_widget = parent
        self.xml_styles = xml_styles or {}
        self.video_settings = dict(video_settings) if video_settings else {
            'fps': 30,
            'width': 1080,
            'height': 1920,
            'srt_pause_threshold': 0.2,
            'srt_max_chars': 40,
        }
        self.groq_settings = dict(groq_settings) if groq_settings else {
            'api_key': '',
            'model': 'openai/gpt-oss-120b',
        }
        
        self.groq_qsettings = QSettings("pyMediaTools", "Groq")
        
        self.setup_ui()
        apply_common_style(self)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("字幕与样式设置")
        title_font = title_label.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        self.tabs = QTabWidget()
        
        # General Settings Tab
        self.general_tab = QWidget()
        gen_layout = QVBoxLayout(self.general_tab)
        
        groq_group = QGroupBox("Groq API 配置")
        groq_layout = QVBoxLayout(groq_group)
        
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("在此输入你的 Groq API Key")
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        initial_key = self.groq_settings.get("api_key") or self.groq_qsettings.value("api_key", "")
        self.txt_api_key.setText(str(initial_key))
        groq_layout.addWidget(QLabel("API Key:"))
        groq_layout.addWidget(self.txt_api_key)
        
        self.txt_groq_model = QLineEdit()
        self.txt_groq_model.setPlaceholderText("openai/gpt-oss-120b")
        initial_model = self.groq_settings.get("model") or self.groq_qsettings.value("model", "openai/gpt-oss-120b")
        self.txt_groq_model.setText(str(initial_model))
        groq_layout.addWidget(QLabel("分析模型:"))
        groq_layout.addWidget(self.txt_groq_model)
        
        gen_layout.addWidget(groq_group)

        # 视频与字幕分段设置
        video_group = QGroupBox("视频与字幕分段设置 (FCPXML & SRT)")
        video_grid = QGridLayout(video_group)
        video_grid.setSpacing(10)

        self.combo_res = QComboBox()
        self.combo_res.addItems(["1080p (1920x1080)", "2K (2560x1440)", "4K (3840x2160)"])
        cur_w = int(self.video_settings.get("width", 1080))
        cur_h = int(self.video_settings.get("height", 1920))
        max_dim = max(cur_w, cur_h)
        if max_dim >= 3840:
            self.combo_res.setCurrentIndex(2)
        elif max_dim >= 2560:
            self.combo_res.setCurrentIndex(1)
        else:
            self.combo_res.setCurrentIndex(0)

        self.chk_vertical = QCheckBox("竖屏 (9:16)")
        self.chk_vertical.setChecked(cur_h > cur_w)

        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["24", "25", "30", "50", "60"])
        self.combo_fps.setCurrentText(str(self.video_settings.get("fps", 30)))

        self.spin_max_chars = QSpinBox()
        self.spin_max_chars.setRange(10, 120)
        self.spin_max_chars.setValue(int(self.video_settings.get("srt_max_chars", 40)))

        self.spin_pause_threshold = QDoubleSpinBox()
        self.spin_pause_threshold.setRange(0.05, 2.0)
        self.spin_pause_threshold.setSingleStep(0.05)
        self.spin_pause_threshold.setValue(float(self.video_settings.get("srt_pause_threshold", 0.2)))

        video_grid.addWidget(QLabel("分辨率:"), 0, 0)
        video_grid.addWidget(self.combo_res, 0, 1)
        video_grid.addWidget(self.chk_vertical, 0, 2)
        video_grid.addWidget(QLabel("帧率 (FPS):"), 1, 0)
        video_grid.addWidget(self.combo_fps, 1, 1)
        video_grid.addWidget(QLabel("单行最大字符数:"), 2, 0)
        video_grid.addWidget(self.spin_max_chars, 2, 1)
        video_grid.addWidget(QLabel("停顿断句阈值 (秒):"), 3, 0)
        video_grid.addWidget(self.spin_pause_threshold, 3, 1)

        gen_layout.addWidget(video_group)
        gen_layout.addStretch()
        
        self.tabs.addTab(self.general_tab, "常规设置")
        
        # Style Tabs (Source, Translate, Highlight)
        def wrap_with_scroll(widget):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(widget)
            return scroll

        for key, label in (("source", "原文样式"), ("translate", "翻译样式"), ("highlight", "高亮样式")):
            if key in self.xml_styles:
                panel = SubtitleStylePanel(key, self.xml_styles, self)
                panel.style_changed.connect(self.refresh_style_preview)
                self.tabs.addTab(wrap_with_scroll(panel), label)
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)
        
        self.preview_group = QGroupBox("样式预览")
        preview_layout = QVBoxLayout(self.preview_group)
        self.dialog_preview_label = SubtitlePreviewLabel()
        preview_layout.addWidget(self.dialog_preview_label)
        layout.addWidget(self.preview_group)
        
        self.on_tab_changed(0)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def refresh_style_preview(self, _style_type=None):
        current_tab = self.tabs.currentIndex()
        if 1 <= current_tab <= 3:
            style_types = ["source", "translate", "highlight"]
            style_type = style_types[current_tab - 1]
            if style_type in self.xml_styles:
                self.dialog_preview_label.update_style(self.xml_styles[style_type])
        if self.parent_widget and hasattr(self.parent_widget, "update_preview"):
            self.parent_widget.update_preview()

    def on_tab_changed(self, index):
        self.preview_group.setVisible(index > 0)
        self.refresh_style_preview()

    def get_groq_settings(self) -> dict:
        """返回更新后的 Groq 配置字典。"""
        api_key = self.txt_api_key.text().strip()
        model = self.txt_groq_model.text().strip() or "openai/gpt-oss-120b"
        self.groq_settings["api_key"] = api_key
        self.groq_settings["model"] = model
        return dict(self.groq_settings)

    def get_video_settings(self) -> dict:
        """返回更新后的视频与字幕分段配置字典。"""
        preset = self.combo_res.currentText()
        if "4K" in preset:
            w, h = 3840, 2160
        elif "2K" in preset:
            w, h = 2560, 1440
        else:
            w, h = 1920, 1080

        if self.chk_vertical.isChecked():
            w, h = h, w

        try:
            fps = int(self.combo_fps.currentText())
        except (ValueError, TypeError):
            fps = 30

        self.video_settings.update({
            "fps": fps,
            "width": w,
            "height": h,
            "srt_max_chars": self.spin_max_chars.value(),
            "srt_pause_threshold": round(self.spin_pause_threshold.value(), 2),
        })
        return dict(self.video_settings)
            
    def save_and_accept(self):
        groq_cfg = self.get_groq_settings()
        self.groq_qsettings.setValue("api_key", groq_cfg["api_key"])
        self.groq_qsettings.setValue("model", groq_cfg["model"])
        self.get_video_settings()
        self.accept()


class VoiceLibraryDialog(QDialog):
    """声音库搜索与添加对话框"""
    def __init__(self, parent=None, api_key=None):
        super().__init__(parent)
        self.setWindowTitle("探索 ElevenLabs 声音库")
        self.setMinimumSize(850, 600)
        self.api_key = api_key
        self.next_page_token = None
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索声音名称、标签或描述...")
        self.search_input.returnPressed.connect(self.search_voices)
        
        self.btn_search = QPushButton("🔍 搜索")
        self.btn_search.clicked.connect(self.search_voices)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.btn_search)
        layout.addLayout(search_layout)
        
        # 结果区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
        # 分页按钮
        self.btn_load_more = QPushButton("加载更多...")
        self.btn_load_more.setVisible(False)
        self.btn_load_more.clicked.connect(self.load_more)
        layout.addWidget(self.btn_load_more)
        
        # 底部按钮
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.reject)
        layout.addWidget(self.btn_close, 0, Qt.AlignRight)
        
    def search_voices(self):
        query = self.search_input.text().strip()
        self.clear_results()
        self.next_page_token = None
        self._perform_search(query)
        
    def load_more(self):
        if self.next_page_token:
            self._perform_search(self.search_input.text().strip(), self.next_page_token)
            
    def _perform_search(self, query, token=None):
        self.btn_search.setEnabled(False)
        self.btn_load_more.setEnabled(False)
        
        self.worker = LibrarySearchWorker(self.api_key, search_text=query, page_token=token)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_search_error)
        self.worker.start()
        
    def on_search_finished(self, voices, next_token):
        self.btn_search.setEnabled(True)
        self.next_page_token = next_token
        self.btn_load_more.setVisible(bool(next_token))
        self.btn_load_more.setEnabled(True)
        
        if not voices and not self.results_layout.count():
            self.results_layout.addWidget(QLabel("未找到匹配的声音。"))
            return
            
        for voice_data in voices:
            item = VoiceLibraryItem(voice_data, self.api_key, self.player, self)
            self.results_layout.addWidget(item)
            
    def on_search_error(self, error_msg):
        self.btn_search.setEnabled(True)
        QMessageBox.warning(self, "搜索出错", error_msg)
        
    def clear_results(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

class VoiceLibraryItem(QFrame):
    """声音库中的单个项目"""
    def __init__(self, data, api_key, player, parent=None):
        super().__init__(parent)
        self.data = data
        self.api_key = api_key
        self.player = player
        self.parent_dialog = parent
        self.voice_id = data.get("voice_id")
        self.public_owner_id = data.get("public_owner_id")
        self.preview_url = data.get("preview_url")
        self.name = data.get("name", "Unknown")
        
        self.setFrameShape(QFrame.StyledPanel)
        self.init_style()
        self.setup_ui()
        
    def init_style(self):
        self.setStyleSheet("""
            VoiceLibraryItem {
                background-color: palette(alternate-base);
                border: 1px solid palette(midlight);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 5px;
            }
            VoiceLibraryItem:hover {
                background-color: palette(midlight);
            }
        """)
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        info_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{self.name}</b>")
        name_label.setStyleSheet("font-size: 14px; color: palette(text);")
        info_layout.addWidget(name_label)
        
        category = self.data.get("category", "generated")
        display_category = category.capitalize()
        is_free_usable = category == "premade"
        free_badge = " <span style='color: #10b981; font-weight: bold;'>[免费版 API 可用]</span>" if is_free_usable else ""
        
        desc = self.data.get("description", "")
        if desc and len(desc) > 80:
            desc = desc[:77] + "..."
            
        detail_label = QLabel(f"<small>类别: {display_category} | ID: {self.voice_id}{free_badge}</small>")
        detail_label.setStyleSheet("color: palette(mid);")
        info_layout.addWidget(detail_label)
        
        if desc:
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: palette(text);")
            info_layout.addWidget(desc_label)
            
        tags = self.data.get("labels", {})
        if tags:
            tag_text = " | ".join([f"{k}: {v}" for k, v in tags.items()])
            tags_label = QLabel(f"<small>{tag_text}</small>")
            tags_label.setStyleSheet("color: palette(mid);")
            info_layout.addWidget(tags_label)
            
        layout.addLayout(info_layout, 1)
        
        ctrl_layout = QHBoxLayout()
        self.btn_preview = QPushButton("🔊 试听")
        self.btn_preview.setFixedWidth(80)
        self.btn_preview.clicked.connect(self.preview)
        if not self.preview_url:
            self.btn_preview.setEnabled(False)
            
        self.btn_add = QPushButton("➕ 添加")
        self.btn_add.setFixedWidth(80)
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.clicked.connect(self.add_voice)
        
        ctrl_layout.addWidget(self.btn_preview)
        ctrl_layout.addWidget(self.btn_add)
        layout.addLayout(ctrl_layout)
        
    def preview(self):
        if self.preview_url:
            self.player.setSource(QUrl(self.preview_url))
            self.player.play()
            
    def add_voice(self):
        name, ok = QInputDialog.getText(self, "添加声音", f"为声音 '{self.name}' 起一个名字:", QLineEdit.Normal, self.name)
        if ok and name:
            self.btn_add.setEnabled(False)
            self.btn_add.setText("正在添加...")
            self.worker = LibraryAddWorker(self.api_key, public_user_id=self.public_owner_id, voice_id=self.voice_id, new_name=name)
            self.worker.finished.connect(self.on_added)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            
    def on_added(self, voice_id, name):
        QMessageBox.information(self, "成功", f"声音 '{name}' 已成功添加到您的帐户。")
        self.btn_add.setText("已添加")
        self.parent_dialog.accept()
        
    def on_error(self, msg):
        self.btn_add.setEnabled(True)
        self.btn_add.setText("➕ 添加")
        QMessageBox.warning(self, "添加失败", msg)
