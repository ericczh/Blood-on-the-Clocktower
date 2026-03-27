"""剧本路由"""
from flask import render_template, request, redirect, url_for, flash
from routes import script_bp
from services.script_service import ScriptService
from services.character_service import CharacterService
from utils.constants import TYPE_LABELS


@script_bp.route("/")
def list_scripts():
    """剧本列表"""
    scripts = ScriptService.get_all()
    characters = CharacterService.get_all()
    char_map = {c.id: c for c in characters}
    
    return render_template(
        "scripts.html",
        scripts=[s.to_dict() for s in scripts],
        char_map=char_map
    )


@script_bp.route("/<sid>")
def script_detail(sid):
    """剧本详情"""
    script = ScriptService.get_by_id(sid)
    if not script:
        flash('剧本不存在', 'error')
        return redirect(url_for("script.list_scripts"))

    characters = CharacterService.get_all()
    char_map = {c.id: c for c in characters}

    script_dict = script.to_dict()
    selected_characters = [
        char_map[cid] for cid in script_dict['characterIds']
        if cid in char_map
    ]

    grouped = {}
    for character in selected_characters:
        grouped.setdefault(character.type, []).append(character)

    return render_template(
        "script_detail.html",
        script=script_dict,
        characters=selected_characters,
        grouped=grouped,
        type_labels=TYPE_LABELS,
    )


@script_bp.route("/new", methods=["GET", "POST"])
def create_script():
    """创建剧本"""
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        character_ids = request.form.getlist('characters')
        
        if not name:
            flash('请输入剧本名称', 'error')
            return redirect(url_for("script.create_script"))
        
        ScriptService.create(name, character_ids)
        flash('剧本创建成功', 'success')
        return redirect(url_for("script.list_scripts"))
    
    grouped = CharacterService.get_grouped()
    return render_template(
        "script_edit.html",
        script=None,
        grouped=grouped,
        type_labels=TYPE_LABELS,
        selected_ids=set()
    )


@script_bp.route("/<sid>/edit", methods=["GET", "POST"])
def edit_script(sid):
    """编辑剧本"""
    script = ScriptService.get_by_id(sid)
    if not script:
        flash('剧本不存在', 'error')
        return redirect(url_for("script.list_scripts"))
    
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        character_ids = request.form.getlist('characters')
        
        if not name:
            flash('请输入剧本名称', 'error')
            return redirect(url_for("script.edit_script", sid=sid))
        
        ScriptService.update(sid, name=name, character_ids=character_ids)
        flash('剧本更新成功', 'success')
        return redirect(url_for("script.list_scripts"))
    
    grouped = CharacterService.get_grouped()
    script_dict = script.to_dict()
    selected_ids = set(script_dict['characterIds'])
    
    return render_template(
        "script_edit.html",
        script=script_dict,
        grouped=grouped,
        type_labels=TYPE_LABELS,
        selected_ids=selected_ids
    )


@script_bp.route("/<sid>/delete", methods=["POST"])
def delete_script(sid):
    """软删除剧本"""
    from config import Config
    password = request.form.get('admin_password')
    if password != Config.ADMIN_PASSWORD:
        flash('权限错误：管理员密码不正确', 'error')
        return redirect(url_for("script.list_scripts"))

    if ScriptService.soft_delete(sid):
        flash('剧本已删除（可恢复）', 'success')
    else:
        flash('删除失败', 'error')
    return redirect(url_for("script.list_scripts"))


@script_bp.route("/<sid>/restore", methods=["POST"])
def restore_script(sid):
    """恢复剧本"""
    if ScriptService.restore(sid):
        flash('剧本已恢复', 'success')
    else:
        flash('恢复失败', 'error')
    return redirect(url_for("script.list_scripts"))
