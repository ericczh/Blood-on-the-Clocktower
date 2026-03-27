"""角色路由"""
from flask import render_template, request, redirect, url_for, flash
from routes import character_bp
from services.character_service import CharacterService
from services.file_service import FileService
from config import Config
from utils.constants import TYPE_LABELS


@character_bp.route("/")
def list_characters():
    """角色列表"""
    grouped = CharacterService.get_grouped()
    return render_template("characters.html", grouped=grouped, type_labels=TYPE_LABELS)


@character_bp.route("/new", methods=["GET", "POST"])
def create_character():
    """创建角色"""
    if request.method == "POST":
        data = _extract_character_data()
        CharacterService.create(data)
        flash('角色创建成功', 'success')
        return redirect(url_for("character.list_characters"))
    
    return render_template("character_edit.html", char=None, type_labels=TYPE_LABELS)


@character_bp.route("/<cid>/edit", methods=["GET", "POST"])
def edit_character(cid):
    """编辑角色"""
    character = CharacterService.get_by_id(cid)
    if not character:
        flash('角色不存在', 'error')
        return redirect(url_for("character.list_characters"))
    
    if request.method == "POST":
        old_image = character.image
        data = _extract_character_data()
        
        # 处理图片变更
        new_image = data.get('image', '')
        if old_image and old_image != new_image:
            FileService.decrement_reference(old_image, Config.UPLOAD_FOLDER)
        if new_image and new_image != old_image:
            FileService.increment_reference(new_image)
        
        CharacterService.update(cid, data)
        flash('角色更新成功', 'success')
        return redirect(url_for("character.list_characters"))
    
    return render_template("character_edit.html", char=character, type_labels=TYPE_LABELS)


@character_bp.route("/<cid>/delete", methods=["POST"])
def delete_character(cid):
    """软删除角色"""
    password = request.form.get('admin_password')
    if password != Config.ADMIN_PASSWORD:
        flash('权限错误：管理员密码不正确', 'error')
        return redirect(url_for("character.list_characters"))

    if CharacterService.soft_delete(cid):
        flash('角色已删除（可恢复）', 'success')
    else:
        flash('删除失败', 'error')
    return redirect(url_for("character.list_characters"))


@character_bp.route("/<cid>/restore", methods=["POST"])
def restore_character(cid):
    """恢复角色"""
    if CharacterService.restore(cid):
        flash('角色已恢复', 'success')
    else:
        flash('恢复失败', 'error')
    return redirect(url_for("character.list_characters"))


def _extract_character_data():
    """从表单提取角色数据"""
    data = {
        'id': request.form.get('id', '').strip(),
        'name': request.form.get('name', '').strip(),
        'nameEn': request.form.get('nameEn', '').strip(),
        'type': request.form.get('type', 'townsfolk'),
        'ability': request.form.get('ability', '').strip(),
        'causeDrunk': bool(request.form.get('causeDrunk')),
        'causePoison': bool(request.form.get('causePoison')),
    }
    
    # 处理图片：优先URL，其次上传文件
    image_url = request.form.get('image_url', '').strip()
    if image_url:
        data['image'] = image_url
    else:
        file = request.files.get('image_file')
        if file and file.filename:
            filename = FileService.save_upload(
                file, Config.UPLOAD_FOLDER, Config.ALLOWED_EXTENSIONS
            )
            if filename:
                data['image'] = filename
    
    # 可选数字字段
    for field in ('firstNight', 'otherNights'):
        val = request.form.get(field, '').strip()
        if val:
            try:
                data[field] = int(val)
            except ValueError:
                pass
    
    return data
