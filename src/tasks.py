from sqlmodel import SQLModel, Field

# defining task class with repo architecture
class Task(SQLModel, table=True):
    id:int = Field(default=None, primary_key=True)
    assigner:str # name of task assigner (someone from admins list)
    assignee:str # to whom task is assigned 
    detail:str
    task_status:str # done, pending etc, to be modified by user