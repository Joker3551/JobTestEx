from fastapi import FastAPI, HTTPException, Query
from app.database import Base, engine, sessionDep
from app.models import Department, Employee
from app.schemas import DepartmentSchema, EmployeerSchema, DepartmentUpdateSchema
from sqlalchemy import update, select

app = FastAPI()

@app.post("/setup_db")
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
@app.post("/departments")
def add_department(data: DepartmentSchema, session: sessionDep):
    parent_id = data.parent_id or None
    
    if parent_id:
        parent = session.get(Department, data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=404,
                detail=f"Департамент родитель не найден"
            )
        message = f"Дочерний департамент {data.name} создан в департаменте {parent.name}"
        exists = session.execute(
            select(Department.id)
            .where(
                Department.parent_id == parent_id,
                Department.name == data.name
            )
        ).first()
    
        if exists:
            raise HTTPException(
                status_code=409,
                detail=f"Название департамента должно быть уникально в пределах одного родителя "
            )
        
    else:
        message = f"Департамент {data.name} успешно создан"
        
        
    new_department = Department(
        name=data.name,
        parent_id=parent_id
    )
    session.add(new_department)
    session.commit()   
        
    return{"message":message, "res":{
                                    "name":data.name,
                                    "parent_id": data.parent_id
                                    }}


@app.post("/department/{id}/employees")
def add_employee(id: int, data: EmployeerSchema, session: sessionDep):
    
    department = session.get(Department, id)
    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Департамент не найден"
        )
    
    new_employee = Employee(
        department_id=id,
        full_name = data.full_name,
        position= data.position,
        hired_at=data.hired_at
    )
    session.add(new_employee)
    session.commit()
    return {
        "message": (f"Сотрудник {data.full_name} на позицию {data.position} успешно нанят " 
                   + (f"{data.hired_at.strftime('%d.%m.%Y')} числа" if data.hired_at else "")
                   ),
        "res": new_employee
        }

#-------------Рекурсия получения подразделений---------------------
def get_children(session, parent_id: int, depth: int):
    if depth == 0:
        return []
    
    children = session.query(Department)\
        .filter(Department.parent_id == parent_id)\
        .all()
    
    result=[]
    for child in children:
        result.append({
            "id": child.id,
            "name": child.name,
            "children": get_children(session, child.id, depth - 1)
            })
    return result
#-----------------------------------------------------------------

@app.get("/departments/{id}")
def get_department_and_all_details(
        id: int,
        session: sessionDep,
        depth: int = Query(1, ge=1, le=5),
        include_employees: bool = Query(True)
    ):
    department = session.get(Department, id)
    children = get_children(session, id, depth)  
    if include_employees:
        employees = session.query(Employee)\
        .filter(Employee.department_id == id)\
        .all()
        list_employees = []
        for employee in employees:
            list_employees.append({
                "id": employee.id,
                "name": employee.full_name,
                "position": employee.position,
                "hired_at": employee.hired_at
            })
        
    
    result={
        "Main_Dep": {
            "id":id,
            "name": department.name
        },
        "Employees": list_employees,
        "ChildrenTree": children
    }
    
    return {"result": result}


#----------------------------Проверка на цикл----------------------------
def is_cycle(session, candidat_id:int, dep_id:int) -> bool:
    
    cur_dep=session.get(Department,candidat_id)
    
    while cur_dep:
        if cur_dep.parent_id == dep_id:
            return True
        cur_dep = session.get(Department, cur_dep.parent_id)

    return False
#------------------------------------------------------------------------

@app.patch("/departments/{id}")
def updatw_department(id:int, session: sessionDep, data: DepartmentUpdateSchema):
    department = session.get(Department, id)
    
    if not department:
        raise HTTPException(status_code=404, detail="Департамент не найден")
    
    if data.name is not None:
        department.name = data.name
    
    if data.parent_id is not None:
        if data.parent_id == id:
            raise HTTPException(status_code=400, detail="Нельзя сделать себя родителем")
        
        new_parent = session.get(Department, data.parent_id)
        if not new_parent:
            raise HTTPException(status_code=404, detail="Родитель не найден")
        
        if is_cycle(session, data.parent_id, id):
            raise HTTPException(status_code=400,detail="Нельзя перемесить себя в своё же поддерево")
        
        department.parent_id =data.parent_id
    
    session.commit()
    session.refresh(department)
    
    return {"res": department}


@app.delete("/departments/{id}", status_code=200)
def delete_department(
                    id: int,
                    session: sessionDep,
                    mode: str = Query(..., pattern="^(cascade|reassign)$"),
                    reassign_to_department_id: int | None = None,
                ):
    
    department = session.get(Department, id)
    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Департамент не найден"
        )
        
    if mode == "reassign":
        if not reassign_to_department_id:
            raise HTTPException(
                400,
                "Поле reassign_to_department_id должно быть заполнено"
            )
        if reassign_to_department_id == id:
            raise HTTPException(400, "Невозможно перевестись в тот же департамент")
        
        new_department = session.get(Department, reassign_to_department_id)
        if not new_department:
            raise HTTPException(404, "Целевой департамент не найден")
        
        session.execute(
            update(Employee)
            .where(Employee.department_id == id)
            .values(department_id=reassign_to_department_id))
        if department.parent_id:
            prev_parent=session.get(Department, department.parent_id)
            parent=prev_parent.id
        else:
            parent=None
            
        session.execute( 
                update(Department)
                .where(Department.parent_id == id)
                .values(parent_id=parent))
        reass_to_dep_id = session.get(Department, reassign_to_department_id)
        message = f"Департамент {department.name} удалён, а его сотрудники перешли в Департамент {reass_to_dep_id.name}"
    else:
        message="Департамент, сотрудники и все его дочернии элементы удалены"
    session.delete(department)
    session.commit()
    return{"ok":True, "message":message}