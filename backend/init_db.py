from app import create_app
from models import db, Department
import json

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created.")

    # Seed departments if empty
    if Department.query.count() == 0:
        departments = [
            {
                "name": "呼吸内科",
                "category": "内科",
                "description": "诊治呼吸系统疾病，如感冒、肺炎、哮喘、支气管炎、咳嗽、咳痰等",
                "symptoms": json.dumps(["咳嗽", "咳痰", "气喘", "胸闷", "呼吸困难", "发烧", "感冒", "流涕", "鼻塞", "咽痛", "打喷嚏", "咯血"]),
                "advice": "如有发热、咳嗽、呼吸困难等症状请及时就诊；就诊前避免吸烟和剧烈运动"
            },
            {
                "name": "心血管内科",
                "category": "内科",
                "description": "诊治心脏和血管疾病，如高血压、冠心病、心律失常、心慌、胸痛等",
                "symptoms": json.dumps(["胸痛", "心慌", "心悸", "胸闷", "气短", "头晕", "血压高", "心跳快", "心痛", "心律不齐"]),
                "advice": "就诊前请保持平静，可携带近期血压测量记录；如剧烈胸痛请立即急诊"
            },
            {
                "name": "消化内科",
                "category": "内科",
                "description": "诊治消化系统疾病，如胃炎、胃溃疡、腹泻、便秘、腹痛、消化不良等",
                "symptoms": json.dumps(["腹痛", "胃痛", "腹泻", "便秘", "恶心", "呕吐", "反酸", "胃胀", "消化不良", "便血", "嗳气", "食欲不振"]),
                "advice": "就诊前建议空腹，可能需要做胃镜或肠镜检查"
            },
            {
                "name": "神经内科",
                "category": "内科",
                "description": "诊治神经系统疾病，如头痛、头晕、失眠、面瘫、帕金森病等",
                "symptoms": json.dumps(["头痛", "头晕", "眩晕", "失眠", "面瘫", "手脚麻木", "抽搐", "记忆力减退", "手抖", "偏头痛"]),
                "advice": "建议详细记录头痛或头晕发作的时间、频率和诱因"
            },
            {
                "name": "骨科",
                "category": "外科",
                "description": "诊治骨骼、关节、脊柱疾病及运动损伤，如骨折、颈椎病、腰椎病、关节炎等",
                "symptoms": json.dumps(["腰痛", "腿痛", "关节痛", "骨折", "扭伤", "颈椎痛", "肩痛", "膝盖痛", "背痛", "脚痛", "手腕痛", "脱臼"]),
                "advice": "如有明显外伤或剧痛，建议先拍X光片；慢性疼痛可携带既往检查资料"
            },
            {
                "name": "皮肤科",
                "category": "专科",
                "description": "诊治皮肤相关疾病，如湿疹、皮炎、痤疮、荨麻疹、脱发等",
                "symptoms": json.dumps(["皮疹", "皮肤痒", "红疹", "痘痘", "痤疮", "脱发", "湿疹", "荨麻疹", "色斑", "痣", "皮肤干燥", "过敏"]),
                "advice": "就诊前不要涂抹药膏或化妆品，以便医生准确观察皮肤状况"
            },
            {
                "name": "眼科",
                "category": "专科",
                "description": "诊治眼部疾病，如近视、白内障、青光眼、结膜炎、视力模糊等",
                "symptoms": json.dumps(["眼痛", "视力模糊", "眼干", "流泪", "红眼", "结膜炎", "飞蚊症", "畏光", "眼痒", "视力下降", "复视"]),
                "advice": "就诊前不要揉眼，隐形眼镜佩戴者请携带镜盒"
            },
            {
                "name": "耳鼻喉科",
                "category": "专科",
                "description": "诊治耳、鼻、咽喉疾病，如中耳炎、鼻炎、咽炎、扁桃体炎等",
                "symptoms": json.dumps(["耳鸣", "耳痛", "流鼻血", "鼻炎", "鼻塞", "打喷嚏", "咽痛", "声音嘶哑", "听力下降", "咽喉痛", "扁桃体炎", "流涕"]),
                "advice": "耳部不适者就诊前勿自行掏耳；鼻部症状请勿使用血管收缩剂滴鼻液"
            },
            {
                "name": "妇产科",
                "category": "专科",
                "description": "诊治女性生殖系统疾病、孕期管理及分娩等",
                "symptoms": json.dumps(["月经不调", "痛经", "白带异常", "下腹痛", "孕期检查", "更年期", "乳房胀痛", "妇科炎症", "不孕"]),
                "advice": "妇科检查建议避开月经期；孕期检查请携带产检本"
            },
            {
                "name": "儿科",
                "category": "专科",
                "description": "诊治0-14岁儿童各类疾病，包括发热、咳嗽、腹泻、发育评估等",
                "symptoms": json.dumps(["小儿发热", "小儿咳嗽", "小儿腹泻", "小儿呕吐", "食欲不振", "哭闹", "发育迟缓", "出疹"]),
                "advice": "就诊时请携带儿童预防接种本；如实告知医生孩子的体重和过敏史"
            },
            {
                "name": "内分泌科",
                "category": "内科",
                "description": "诊治内分泌和代谢疾病，如糖尿病、甲亢、甲减、肥胖症等",
                "symptoms": json.dumps(["多饮", "多尿", "体重下降", "肥胖", "怕热", "怕冷", "手抖", "心悸", "易怒", "乏力", "口渴", "多食"]),
                "advice": "糖尿病疑似患者建议空腹前来就诊，可能需要抽血检查血糖"
            },
            {
                "name": "泌尿外科",
                "category": "外科",
                "description": "诊治泌尿系统和男性生殖系统疾病，如肾结石、前列腺疾病等",
                "symptoms": json.dumps(["尿频", "尿急", "尿痛", "血尿", "腰痛", "排尿困难", "尿不尽", "夜尿多"]),
                "advice": "就诊前建议憋尿以便做B超检查；结石患者请多饮水"
            },
        ]

        for dept_data in departments:
            dept = Department(**dept_data)
            db.session.add(dept)

        db.session.commit()
        print(f"Seeded {len(departments)} departments.")

    print("Database initialization complete.")
