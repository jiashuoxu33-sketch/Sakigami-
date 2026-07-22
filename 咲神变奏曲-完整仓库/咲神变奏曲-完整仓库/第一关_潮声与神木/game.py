# 《咲神变奏曲》· 第一关：潮声与神木
# 游戏引擎 - AI可玩版（修复版 v1.1）


class SakiGame:
    def __init__(self):
        self.location = "偏殿"
        self.mind = 100
        self.trust = {"铃": 50, "玄海": 40, "空海": 50}
        self.talk_rounds = {"铃": 0, "玄海": 0, "空海": 0}
        self.time = 0
        self.paper = 5
        self.clues = []
        self.items = ["画笔", "矿物颜料", "油灯"]
        self.over = False
        self.ending = None
        self.flags = {
            "井口观察次数": 0, "短刃观察次数": 0, "画像观察次数": 0,
            "经卷观察次数": 0, "贝壳观察次数": 0,
            "已坠井": False, "已打捞": False, "见过柴房工具": False,
            "发现凹槽": False, "倒影微笑": False, "铃已移动": False,
            "时间警告": False,
        }
        # NPC 初始位置：铃刚报完信，还在偏殿；进入本殿后她会退到后院
        self.npc_locations = {"铃": "偏殿", "玄海": "经堂", "空海": "客房"}
        self.scenes = {
            "偏殿": self.scene_biaside, "本殿": self.scene_honden,
            "后院": self.scene_kouro, "经堂": self.scene_kyoudou,
            "客房": self.scene_kyakubou,
        }
        self.npcs = {"铃": self.npc_suzu, "玄海": self.npc_genkai, "空海": self.npc_kukai}

    # ---------- 工具 ----------
    def add_clue(self, name):
        if name not in self.clues:
            self.clues.append(name)

    def add_item(self, name):
        if name not in self.items:
            self.items.append(name)

    def change_mind(self, delta):
        self.mind = max(0, min(100, self.mind + delta))
        if self.mind <= 0 and not self.over:
            self.trigger_ending_c()

    # ---------- 指令入口 ----------
    def cmd(self, raw_input):
        parts = raw_input.strip().split()
        if not parts:
            return "请输入指令。输入 help 查看可用指令。"
        if self.over:
            if parts[0].lower() == "new_game":
                self.__init__()
                return "【新游戏开始】你又一次在偏殿醒来，油灯还亮着。输入 look 重新开始调查。"
            return f"游戏已结束（{self.ending}）。输入 new_game 重新开始。"
        action = parts[0].lower()
        arg = " ".join(parts[1:]) if len(parts) > 1 else ""
        if action == "help":
            return ("可用指令：look / look [对象] · search [对象] · talk [人物] · go [地点] · "
                    "think · items · paint [描述] · rest · accuse [对象] · status")
        if action == "look":
            return self.do_look(arg)
        if action == "search":
            return self.do_search(arg)
        if action == "talk":
            return self.do_talk(arg)
        if action == "go":
            return self.do_go(arg)
        if action == "think":
            return self.do_think()
        if action == "items":
            return self.do_items()
        if action == "paint":
            return self.do_paint(arg)
        if action == "rest":
            return self.do_rest()
        if action == "accuse":
            return self.do_accuse(arg)
        if action == "status":
            return (f"📍 {self.location} · 🧠 心智 {self.mind}/100 · ⏳ 时间 {self.time}% · "
                    f"📋 线索 {len(self.clues)} 条 · 信任 {self.trust}")
        return f"未知指令：{action}。输入 help 查看可用指令。"

    # ---------- 观察 / 搜索 ----------
    def do_look(self, arg):
        if not arg:
            return self.scenes[self.location]("look")
        if arg in self.scenes and arg != self.location:
            return f"你现在看不见{arg}那边。用 go {arg} 走过去再看。"
        if arg in ("贝壳", "七芒星贝壳"):
            return self.look_shell()
        return self.scenes[self.location](f"look {arg}")

    def do_search(self, arg):
        if not arg:
            return "search 什么？例如：search 井沿 / search 布囊 / search 井底"
        if self.location == "后院" and arg in ("井沿", "井口外侧", "井沿外侧"):
            if not self.flags["发现凹槽"]:
                self.flags["发现凹槽"] = True
                self.add_clue("井沿凹槽")
                return ("你绕到井沿外侧，拨开颜色不均的苔藓——那里有一个凹槽。凹槽是空的，但内壁残留着油布纤维，"
                        "底部的青苔上有一个清晰的贝壳形压痕。\n【获得线索：井沿凹槽】包裹曾在这里，如今应当落进了井中。"
                        "也许可以用工具打捞（search 井底）。")
            return "凹槽空着，压痕还在。东西应该在井底。"
        if self.location == "后院" and arg == "井底":
            if "七芒星贝壳" in self.items:
                return "井底只剩水和青砖。包裹已经在你手里了。"
            if not self.flags["见过柴房工具"]:
                return "井太深，徒手够不到底。你需要工具——柴房里也许有什么能用的（先去看看柴房）。"
            self.change_mind(-5)
            self.flags["已打捞"] = True
            self.add_clue("井壁刻字")
            self.add_clue("七芒星贝壳")
            self.add_item("七芒星贝壳")
            return ("你用柴房借来的木桶绑上绳子，在井底青砖边慢慢打捞。不一会儿，桶里多了一个油布包裹——"
                    "里面是一枚刻着七芒星的贝壳。借着油灯，你还看见井壁上有一行刻字：『我看到了。潮水之下。』\n"
                    f"心智 -5（当前：{self.mind}）\n【获得：七芒星贝壳、井壁刻字】")
        if self.location == "客房" and arg == "布囊":
            return self.scene_kyakubou("look 剪刀")
        return "你仔细搜了一遍，没有发现新的东西。"

    # ---------- 对话 ----------
    def do_talk(self, arg):
        if arg not in self.npcs:
            return f"没有叫 {arg} 的人在这里。"
        if self.npc_locations[arg] != self.location:
            return f"{arg}现在不在这里。她/他可能在【{self.npc_locations[arg]}】。"
        self.talk_rounds[arg] += 1
        self.trust[arg] = min(100, self.trust[arg] + 10)
        return self.npcs[arg]()

    # ---------- 移动 ----------
    def do_go(self, arg):
        valid = list(self.scenes.keys())
        if arg not in valid:
            return f"无法前往 {arg}。可前往：{', '.join(valid)}"
        self.location = arg
        extra = ""
        if arg == "本殿" and not self.flags["铃已移动"]:
            self.flags["铃已移动"] = True
            self.npc_locations["铃"] = "后院"
            extra = "\n（铃没有跟进来。她低着头，退回了后院的方向。）"
        return f"你来到了 {arg}。\n{self.scenes[arg]('look')}{extra}"

    # ---------- 思考 ----------
    def do_think(self):
        lines = ["你整理了目前已知的线索："]
        mapping = {
            "香炉贝壳": "- 【香炉中的半片贝壳】刻有『忆』字，与神主遗言呼应。",
            "井壁刻字": "- 【井壁刻字】『我看到了。潮水之下。』",
            "七芒星贝壳": "- 【七芒星贝壳】七角数字：3,7,11,15,19,23,42。",
            "经卷压痕": "- 【经卷背面压痕】『神堕者，非神所堕，乃人所见之人心之暗也。』",
            "逃字": "- 【画像中的『逃』字】前任神主玄岳留下的警示。",
            "铁剪刀": "- 【铁剪刀】空海布囊中发现的物证，柄上绑着一根黑发。",
            "木桶刻字": "- 【柴房木桶刻字】『铃、玄海、空海』——三人被关联，还有一个被刮掉的名字，尾字是『岳』。",
            "刃中幻象": "- 【刃中幻象】你看到了前任神主玄岳的脸。",
            "井沿凹槽": "- 【井沿凹槽】油布纤维与贝壳压痕——包裹曾被藏在井沿外侧。",
            "尸体姿势": "- 【尸体姿势】右手前伸，食指弯曲，指向门槛。",
            "油灯未燃": "- 【经堂油灯】灯芯干硬，从未点燃过。",
        }
        for k, v in mapping.items():
            if k in self.clues:
                lines.append(v)
        contra = []
        if "铃证词" in self.clues and "尸体姿势" in self.clues:
            contra.append("⚠️ 铃说自己一直在井边打水，却能准确说出尸体『食指弯曲指向门槛』的细节——那要走进本殿、从经堂一侧近看才能看清。")
        if "玄海证词" in self.clues and "油灯未燃" in self.clues:
            contra.append("⚠️ 玄海说他在经堂抄经、离开时吹熄了油灯——但灯芯从未点燃过，灯油满盈。")
        if "空海证词" in self.clues:
            contra.append("⚠️ 空海说他在廊下『望月』——可案发当晚是朔日，根本没有月亮。他自己也圆不下去。")
        if contra:
            lines.append("—— 你在意的矛盾 ——")
            lines.extend(contra)
        if len(lines) == 1:
            lines.append("（目前还没有任何线索。去调查吧。）")
        return "\n".join(lines)

    def do_items(self):
        return f"随身物品：{', '.join(self.items)}，画纸（{self.paper}张）"

    # ---------- 作画 / 休息 ----------
    def do_paint(self, arg):
        if self.paper <= 0:
            return "你没有画纸了。"
        self.paper -= 1
        self.change_mind(+15)
        return (f"你蘸取颜料，在纸上描绘着脑海中的景象。笔尖游走，心神渐宁。"
                f"心智 +15（当前：{self.mind}），剩余画纸 {self.paper} 张。")

    def do_rest(self):
        self.change_mind(+10)
        self.time += 10
        extra = ""
        if self.time >= 80 and not self.flags["时间警告"]:
            self.flags["时间警告"] = True
            extra = "\n远处传来第一声太鼓——祭典前夜仪式快要开始了。留给你的时间不多了。"
        return (f"你合上眼，听着窗外的潮声，小憩片刻。心智 +10（当前：{self.mind}）。"
                f"时间推进至 {self.time}%。{extra}")

    # ---------- 指认与结局 ----------
    def do_accuse(self, arg):
        if not arg:
            return "accuse 谁？（铃 / 玄海 / 空海）——或者，你怀疑的是『咲神』？"
        if arg == "咲神":
            need = {"七芒星贝壳", "经卷压痕", "刃中幻象"}
            if need.issubset(set(self.clues)):
                self.over = True
                self.ending = "结局B · 神堕之醒"
                return ("【结局B · 神堕之醒】\n你把七芒星贝壳、经卷压痕和刃中幻象一一摆开。\n"
                        "『凶手不是人。』你说。『咲神不是神明，是一种活在记忆里的东西——它读取人心的暗处，"
                        "再把人变成它的形状。神主不是被杀的，是被「清除」的。』\n"
                        "铃哭了。玄海闭上了眼。空海收起了笑容。\n"
                        "你把贝壳和那幅未完成的画卷一起封进地窖。潮声在门外退去了半步——只是半步。\n"
                        "（真相结局 · 古代篇完。古画将沉睡至2026年。）")
            missing = need - set(self.clues)
            return (f"你说出了『咲神』两个字。风停了半秒——但你拿不出足够的证据支撑这个答案。"
                    f"还缺：{'、'.join(missing)}。")
        if arg in self.npcs:
            if len(self.clues) < 5:
                return (f"你指认了{arg}，但证据链太薄（当前线索 {len(self.clues)} 条，至少需要 5 条）。"
                        "再调查一下吧。")
            self.over = True
            self.ending = "结局A · 人犯之罪"
            return (f"【结局A · 人犯之罪】\n你指认了{arg}。证据、证词、矛盾点——链条完整，逻辑通顺。\n"
                    f"{arg}没有辩解。岛民们松了一口气：是人的罪，不是神的怒。这样就好。\n"
                    "只有你知道，井底那行字、刃中那张脸、贝壳上那个「42」——都没有答案。\n"
                    "真相被掩盖为岛上的内斗。古画被封存进地窖，等待两百年后的挖掘机。\n"
                    "（普通结局 · 古代篇完。）")
        return f"你不能指认「{arg}」。"

    def trigger_ending_c(self):
        self.over = True
        self.ending = "结局C · 神堕结局"
        self._ending_c_text = ("【结局C · 神堕结局】\n你的心智终于支撑到了极限。\n"
                               "岛民们的脸在你眼里变成了空洞的人形轮廓。潮声在对你说话——用你自己的声音。\n"
                               "你成为了岛上新的「神堕者」。\n（Bad End。输入 new_game 重新开始。）")

    # ---------- 贝壳观察链 ----------
    def look_shell(self):
        if "七芒星贝壳" not in self.items:
            return "你还没有拿到那枚贝壳。"
        self.flags["贝壳观察次数"] += 1
        n = self.flags["贝壳观察次数"]
        if n == 1:
            return "贝壳内壁刻着七芒星，七个角分别标着数字：3, 7, 11, 15, 19, 23, 42。线条细得不像人力所为。"
        if n == 2:
            return ("你重新读那串数字：3、7、11、15、19、23——前六个角，相邻差值都是 4，是标准的等差序列。"
                    "按这个规律，第七个角本应是 27——可那里刻的是 42。\n"
                    "被跳过的不是中间的任何一项，而是「27」这个应然之位。42……也许不是数字，而是某个年份，或坐标。")
        if "经卷压痕" in self.clues:
            return ("你把贝壳对着经卷压痕那行字：『神堕者……乃人所见之人心之暗也。』\n"
                    "七个角，也许对应七种人心之暗——贪婪、恐惧、愤怒、嫉妒、傲慢、冷漠……"
                    "而那个不属于等差序列的 42，是「被遗忘的第八种」。那是咲神真正的源头。")
        return "你觉得这串数字还缺一块拼图——也许经堂那卷经卷的背面，藏着解读它的钥匙。"

    # ---------- 场景 ----------
    def scene_biaside(self, action):
        if action == "look":
            return "你的临时画室。墙上挂着几幅未完成的岛景速写。案上摊着颜料、画笔和画纸。油灯的火苗微微晃动。窗外海雾浓稠。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "油灯":
                return "灯油充足，火苗稳定。灯盏底座刻着一个『咲』字。"
            if obj == "画纸":
                return f"空白画纸，还剩 {self.paper} 张。"
            if obj == "窗户":
                return "窗外只有浓雾和黑暗。隐约能听到潮声。"
            if obj == "速写":
                return "你画的岛景：礁石、海鸟、老樱树。其中一张——你画了一朵红色的云。"
            return f"没有什么特别的 {obj}。"
        return "你在偏殿。可用指令：look, look [对象], talk [人物], go [地点], think, items, paint, rest"

    def scene_honden(self, action):
        if action == "look":
            return "本殿比偏殿大得多，正中央的祭坛上供奉着一尊模糊的木雕神像。神主的尸体倒在祭坛前，面朝下，胸口插着一把透明的短刃。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "尸体":
                self.add_clue("尸体姿势")
                return ("神主的尸体面朝下，右手向前伸出，食指微微弯曲，指尖几乎触及门槛——"
                        "不像是自然的松弛，更像最后一刻想指什么。\n【获得线索：尸体姿势】")
            if obj in ("短刃", "凶器"):
                self.flags["短刃观察次数"] += 1
                c = self.flags["短刃观察次数"]
                if c == 1:
                    return "一把透明的短刃，通体如冰晶，刃身内部有极细的暗红色血管状纹理。没有血迹。"
                if c == 2:
                    self.change_mind(-10)
                    return (f"那些『血管』似乎在缓慢流动——像是活的。你闻到一股甜腥味。"
                            f"你意识到——这不是刀，是某种凝固的液体。\n心智 -10（当前：{self.mind}）")
                if c == 3:
                    self.change_mind(-30)
                    self.add_clue("刃中幻象")
                    return (f"你无法移开目光。刃身中映出一张老人的面孔——前任神主玄岳。他说：『下一个，是你。』\n"
                            f"心智 -30（当前：{self.mind}）\n【获得线索：刃中幻象】")
                self.change_mind(-5)
                return (f"你逼着自己再看一眼。纹路缓缓蠕动，像是认出了你。理智告诉你该停下了。\n"
                        f"心智 -5（当前：{self.mind}）")
            if obj == "祭坛":
                return "供奉着一尊面目模糊的木雕神像。神像底座刻着一圈古文字。"
            if obj == "神像":
                return "面目漆黑，但头部似乎微微向右偏了一点，像是正看着门槛的方向。"
            if obj == "香炉":
                self.add_clue("香炉贝壳")
                return "线香已燃尽。灰烬中有细碎的贝壳碎片。你翻找片刻，找到半片贝壳，内壁刻着一个『忆』字。\n【获得线索：香炉中的半片贝壳】"
            if obj == "门槛":
                return "木质门槛被磨得光滑。外侧有一道浅划痕，像是指甲刮出来的。"
            return f"没有什么特别的 {obj}。"
        return "你在本殿（案发现场）。可用指令：look, look [对象], talk [人物], go [地点]"

    def scene_kouro(self, action):
        if action == "look":
            return "青石板地面长满湿滑苔藓。中央一口石井。旁边堆着干柴，柴房门半掩。空气中弥漫着海潮的咸腥。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj in ("井口", "井"):
                if "七芒星贝壳" in self.items:
                    return "水面幽暗，映着你的脸。你已经拿到井底的东西了——你不想再多看。"
                self.flags["井口观察次数"] += 1
                c = self.flags["井口观察次数"]
                if c == 1:
                    return "青石井沿，长满苔藓。水面幽暗，倒映着你的脸。"
                if c == 2:
                    self.change_mind(-10)
                    return f"水面异常平静。你的倒影格外清晰——但水中的『你』在微笑。\n心智 -10（当前：{self.mind}）"
                self.change_mind(-25)
                self.flags["已坠井"] = True
                self.flags["倒影微笑"] = True
                self.add_clue("井壁刻字")
                self.add_clue("七芒星贝壳")
                self.add_item("七芒星贝壳")
                return (f"你失去平衡，坠入井中。水很浅，只及腰。你在井底青砖下发现一个油布包裹——"
                        f"里面是一枚刻着七芒星的贝壳。井壁上有一行刻字：『我看到了。潮水之下。』\n"
                        f"心智 -25（当前：{self.mind}）\n【获得：七芒星贝壳、井壁刻字】\n"
                        "（从此，你经过任何水面，都会觉得倒影在笑。）")
            if obj == "柴房":
                self.flags["见过柴房工具"] = True
                return "门半掩，里面堆着干柴和旧渔网。角落有一只翻倒的木桶，旁边还挂着一截绳子——借来打捞东西正合适。"
            if obj == "木桶":
                self.flags["见过柴房工具"] = True
                self.add_clue("木桶刻字")
                return ("你把翻倒的木桶扶正——桶底刻着三个名字：『铃』、『玄海』、『空海』。"
                        "旁边还有一个被刮掉的名字，隐约辨认出最后一个字是『岳』。\n【获得线索：柴房木桶刻字】")
            if obj in ("地面", "水渍"):
                return "青石板上有一些淡水渍，从井口方向延伸向本殿方向。"
            return f"没有什么特别的 {obj}。"
        return "你在后院。可用指令：look, look [对象], search [对象], talk [人物], go [地点]"

    def scene_kyoudou(self, action):
        if action == "look":
            return "经堂像一间密室。墙上挂着一幅泛黄的旧画像。案上摊着一卷打开的经卷，墨已干。旁边一盏油灯，灯油是满的。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "画像":
                self.flags["画像观察次数"] += 1
                c = self.flags["画像观察次数"]
                if c == 1:
                    return "画中是一位身着神官服的老人，面容肃穆。左下角小字：『咲岛神社·前任神主·玄岳，享年六十有三。』"
                if c == 2:
                    return "画中老人的左手食指微微弯曲——姿势与神主尸体的右手几乎一样。"
                self.add_clue("逃字")
                return "你贴近画框左下角，发现一个极淡的字：『逃』。前任神主玄岳在画中留下了警示。\n【获得线索：画像中的『逃』字】"
            if obj == "经卷":
                self.flags["经卷观察次数"] += 1
                if self.flags["经卷观察次数"] == 1:
                    return "抄写的是一段祈福经文。最后几行字迹潦草，像是手在发抖。"
                self.add_clue("经卷压痕")
                return ("你把经卷对着光翻到背面——纸上有压痕，像是用力书写时留下的。你辨认出一行字："
                        "『神堕者，非神所堕，乃人所见之人心之暗也。』\n【获得线索：经卷背面压痕】")
            if obj == "油灯":
                self.add_clue("油灯未燃")
                return ("灯盏冰凉，灯油满盈，灯芯干硬，没有被点燃过的痕迹。灯盏侧面刻着一行小字：『勿信其光』。\n"
                        "【获得线索：经堂油灯】")
            if obj == "桌腿":
                return "桌腿上有新的划痕，像是被绳索勒过的痕迹。"
            return f"没有什么特别的 {obj}。"
        return "你在经堂。可用指令：look, look [对象], talk [人物], go [地点]"

    def scene_kyakubou(self, action):
        if action == "look":
            return "客房简陋。一张薄被褥。旁边放着一个灰色布囊。榻榻米上有一处跪坐的凹陷，正对着窗户。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "布囊":
                return "鼓鼓囊囊，里面有经书、贝壳、干海星。最底下似乎还压着什么硬的东西。"
            if obj in ("剪刀", "铁剪刀"):
                self.add_clue("铁剪刀")
                self.add_item("铁剪刀")
                return "你翻到布囊最底层，摸到一把缺了口的铁剪刀。手柄上绑着一根黑色的头发。\n【获得：铁剪刀】"
            if obj == "榻榻米":
                return "跪坐的凹陷，正对着窗户——窗外是经堂的方向。"
            if obj == "窗户":
                return "窗框上有新鲜的刮痕，像是被扁平的工具撬开过。刮痕宽度与你找到的铁剪刀刃口吻合。"
            return f"没有什么特别的 {obj}。"
        return "你在客房。可用指令：look, look [对象], search [对象], talk [人物], go [地点]"

    # ---------- NPC ----------
    def npc_suzu(self):
        self.add_clue("铃证词")
        if self.talk_rounds["铃"] >= 2 and self.trust["铃"] >= 60:
            return "铃低声说：『我小时候，神主大人告诉我，咲神真正的样子……是「会流淌的东西」。』"
        return ("铃低着头说：『神主大人……他倒在祭坛前。右手向前伸着，手指……手指是弯的，指着门槛。』\n"
                "她停顿了一下，声音更轻：『我……我一直在后院打水，我不敢靠近看。橘先生，那道光……好像在动。』")

    def npc_genkai(self):
        if "七芒星贝壳" in self.items and self.talk_rounds["玄海"] >= 2:
            return ("玄海看到贝壳，脸色骤变：『你从哪里找到的？！那口井……那口井不该被碰。』\n"
                    "他沉默良久，终于松口：『……前任神主之死，另有隐情。咲神不是神。它是从「记忆」里长出来的东西。』")
        if self.talk_rounds["玄海"] >= 2 and self.trust["玄海"] >= 60:
            return "玄海说：『你问那把光做的刀？那不是刀。那是神主的「记忆」被抽出来之后，凝固成的形状。』"
        self.add_clue("玄海证词")
        return ("玄海冷冷地说：『外来者，这不是你该插手的事。神主的死，是咲神的意思。』\n"
                "你问起他案发时的行踪，他闭着眼：『我在经堂抄经。油灯？我离开时吹熄了。也许……是风。』")

    def npc_kukai(self):
        if "铁剪刀" in self.items and self.talk_rounds["空海"] >= 2:
            return ("空海的笑容消失了：『你翻了我的东西啊。那把剪刀……是我从一个女人手里买的。"
                    "她说这是她丈夫最后用过的东西。』")
        if self.talk_rounds["空海"] >= 2 and self.trust["空海"] >= 60:
            return "空海低声说：『我确实不是真僧侣。我是幕府派来的。但这座岛……比我查过的任何案子都奇怪。』"
        self.add_clue("空海证词")
        return ("空海笑着说：『哎呀，橘先生，我们都成了嫌疑人了呢。这可真是有趣的缘分。』\n"
                "你问起他案发时在做什么，他摊开手：『我在廊下看月亮。哦？那天是初一？……那就当我是在看海吧。』")


# ==================== 模块级入口（README 快速开始用） ====================
_game = SakiGame()

def cmd(command):
    """统一指令入口：import game 之后直接 game.cmd('look') 即可游玩。"""
    return _game.cmd(command)

def new_game():
    """开新局。"""
    return _game.cmd("new_game")

# ==================== 命令行入口 ====================
if __name__ == "__main__":
    print("《咲神变奏曲》· 第一关：潮声与神木")
    print("类型：文字推理游戏。输入 help 查看指令。")
    print("你坐在偏殿中，巫女铃刚告诉你：神主死了。")
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ["quit", "exit"]:
                break
            print(cmd(user_input))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"错误：{e}")
