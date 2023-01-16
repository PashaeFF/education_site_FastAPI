from fastapi import APIRouter, Request, UploadFile, Depends, File
from PIL import Image
from sqlalchemy.orm import Session
import configurations.models as models, configurations.database as database, secrets, pathlib
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from utils.helper import templates, check_user_in_site, site_default_variables


user_panel = APIRouter(
    tags=['Site / User']
)

@user_panel.get("/profile/{id}")
def update_profile(id: int, request: Request, db: Session = Depends(database.get_db)):
    check_site_user = check_user_in_site(request)
    if check_site_user['site_settings']:
        if check_site_user['site_settings'].is_active is None:
            return templates.TemplateResponse("site/closed.html", {"request":request})
        else:
            if check_site_user['user']:
                if id == check_site_user['user'].id or check_site_user['user'].admin_user == True or check_site_user['user'].super_user == True:
                    edu = db.query(models.Education).all()
                    categories = db.query(models.EduCategory).all()
                    news_category = db.query(models.NewsCategory).all()
                    profile = db.query(models.User).filter_by(id=id).first()
                    if profile:
                        page_title = profile.name_surname +" - Profil məlumatları"
                    else:
                        return RedirectResponse("/",status_code=HTTP_303_SEE_OTHER)
                    return templates.TemplateResponse("site/route/profile.html", {"request":request, "user":check_site_user['user'], "edu":edu, "categories":categories,
                                                                                "current_user":check_site_user['current_user'], "profile":profile, "news_category":news_category,
                                                                                "page_title":page_title, "site_settings":check_site_user['site_settings']})
                else:
                    return RedirectResponse("/",status_code=HTTP_303_SEE_OTHER)
            else:
                return RedirectResponse("/",status_code=HTTP_303_SEE_OTHER)


@user_panel.get("/update_profile/{id}")
def update_profile(id: int, request: Request, db: Session = Depends(database.get_db)):
    check_site_user = check_user_in_site(request)
    if check_site_user['site_settings']:
        if check_site_user['site_settings'].is_active is None:
            return templates.TemplateResponse("site/closed.html", {"request":request})
        else:
            variables = site_default_variables(request)
            if check_site_user['user']:
                if id == check_site_user['user'].id or check_site_user['user'].admin_user == True or check_site_user['user'].super_user == True:
                    check_id = db.query(models.User).filter_by(id=id).first()
                    page_title = check_id.name_surname +" - Profil məlumatları"
                    return templates.TemplateResponse("site/route/update_profile.html", {"request":request, "user":check_site_user['user'], "edu":variables['educations'], "categories":variables['categories'], "current_user":check_site_user['current_user'],
                                                                                        "news_category":variables['news_category'], "page_title":page_title, "site_settings":check_site_user['site_settings'],
                                                                                        "flash":variables['_flash_message'], "check_id":check_id})
                else:
                    return RedirectResponse("/",status_code=HTTP_303_SEE_OTHER)
            if check_site_user['current_user']:
                check_id = db.query(models.User).filter_by(id=id).first()
                page_title = check_id.name_surname +" - Profil məlumatları"
                return templates.TemplateResponse("site/route/update_profile.html", {"request":request, "user":check_site_user['user'], "edu":variables['educations'], "categories":variables['categories'], "current_user":check_site_user['current_user'],
                                                                                    "news_category":variables['news_category'], "page_title":page_title, "site_settings":check_site_user['site_settings'],
                                                                                    "flash":variables['_flash_message'], "check_id":check_id})
            else:
                return RedirectResponse("/",status_code=HTTP_303_SEE_OTHER)


@user_panel.post("/update_profile/{id}")
async def post_update_profile(id:int, request: Request, db:Session = Depends(database.get_db), file: UploadFile = File(...)):
    check_site_user = check_user_in_site(request)
    if check_site_user['user']:
        if id == check_site_user['user'].id or check_site_user['user'].admin_user == True or check_site_user['user'].super_user == True:
            user = db.query(models.User).filter_by(id=id)
            FILEPATH = "static/profile_pictures/"
            old_profile_picture = user.first().profile_picture
            form = await request.form()
            name_surname = form.get("name_surname")
            phone = form.get("phone")
            age = form.get("age")
            city = form.get("city")
            education = form.get("education")
            certificate_points = form.get("certificate_points")
            about = form.get("about")
            select_university_id = form.get("select_university_id")
            profile_picture = form.get("file")
            request.session["flash_messsage"] = []
            if profile_picture:
                filename = file.filename
                if len(filename) > 0:
                    extension = filename.split(".")[1]
                    if extension not in ["png","jpg","jpeg"]:
                        request.session["flash_messsage"].append({"message": "Yalnız JPG, PNG, JPEG", "category": "error"})
                        request = RedirectResponse(url=f"/update_profile/{id}",status_code=HTTP_303_SEE_OTHER)
                        return request
                    else:
                        token_name = secrets.token_hex(12)+"."+extension
                        generated_name = FILEPATH + token_name
                        file_content = await file.read()
                        with open(generated_name, "wb") as file:
                            file.write(file_content)
                        img = Image.open(generated_name)
                        img.save(generated_name)
                        file.close()
                        if old_profile_picture:
                            old = pathlib.Path(FILEPATH+old_profile_picture)
                            try:
                                old.unlink()
                            except:
                                pass
                        user.update({'name_surname':name_surname, 'age':age, 'city':city, 'profile_picture':token_name, 'phone':phone, 'education':education,
                                    'certificate_points':certificate_points, 'about':about, 'select_university_id':select_university_id},synchronize_session=False)
                        db.commit()
                        request.session["flash_messsage"].append({"message": "Profil tamamlandı", "category": "success"})
                        request = RedirectResponse(url=f"/",status_code=HTTP_303_SEE_OTHER)
                        return request
            user.update({'name_surname':name_surname, 'age':age, 'city':city, 'phone':phone, 'education':education, 'certificate_points':certificate_points,
                        'about':about, 'select_university_id':select_university_id},synchronize_session=False)
            db.commit()
            request.session["flash_messsage"].append({"message": "Profil tamamlandı", "category": "success"})
            request = RedirectResponse(url=f"/",status_code=HTTP_303_SEE_OTHER)
            return request