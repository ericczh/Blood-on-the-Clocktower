"""文件服务"""
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from models import db, FileUpload


class FileService:
    """文件管理业务逻辑"""
    
    @staticmethod
    def save_upload(file, upload_folder, allowed_extensions):
        """保存上传的文件"""
        if not file or not file.filename:
            return None
        
        # 检查文件扩展名
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed_extensions:
            return None
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = Path(upload_folder) / filename
        
        # 确保目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file.save(filepath)
        
        # 记录到数据库
        file_record = FileUpload(
            filename=filename,
            original_name=secure_filename(file.filename),
            file_size=os.path.getsize(filepath),
            mime_type=file.content_type,
            reference_count=1,
        )
        db.session.add(file_record)
        db.session.commit()
        
        return filename
    
    @staticmethod
    def increment_reference(filename):
        """增加文件引用计数"""
        file_record = FileUpload.query.filter_by(filename=filename).first()
        if file_record:
            file_record.increment_reference()
            db.session.commit()
    
    @staticmethod
    def decrement_reference(filename, upload_folder):
        """减少文件引用计数，如果为0则删除文件"""
        if not filename or filename.startswith('http'):
            return
        
        file_record = FileUpload.query.filter_by(filename=filename).first()
        if file_record:
            file_record.decrement_reference()
            
            # 如果引用计数为0，删除文件和记录
            if file_record.reference_count <= 0:
                filepath = Path(upload_folder) / filename
                if filepath.exists():
                    filepath.unlink()
                db.session.delete(file_record)
            
            db.session.commit()
    
    @staticmethod
    def cleanup_unused_files(upload_folder):
        """清理未使用的文件"""
        unused = FileUpload.query.filter_by(reference_count=0).all()
        for file_record in unused:
            filepath = Path(upload_folder) / file_record.filename
            if filepath.exists():
                filepath.unlink()
            db.session.delete(file_record)
        db.session.commit()
        return len(unused)
