# 《咲神变奏曲》· 第二章：东京湾回声
# 游戏引擎 - AI可玩版（修复版 v1.1）


class SakiGameChapter2:
    def __init__(self):
        self.location = "办公室"
        self.mind = 100
        self.time = 0
        self.clues = []
        self.items = ["手机", "笔记本", "笔", "研究所门禁卡"]
        self.over = False
        self.ending = None
        self.talk_rounds = {"佐伯教授": 0, "三浦博士": 0, "管理员": 0, "DJ": 0, "档案管理员": 0}
        self.flags = {
            "办公室_书架_次数": 0, "办公室_桌面_次数": 0, "办公室_窗户_次数": 0,
            "办公室_门背后_次数": 0, "办公室_垃圾桶_次数": 0,
            "化学_显微镜_次数": 0, "化学_窗台_次数": 0,
            "工地_坑洞_次数": 0, "工地_瓦片_次数": 0, "工地_围栏_次数": 0,
            "电台_调音台_次数": 0, "电台_天线_次数": 0,
            "档案_档案柜_次数": 0, "档案_潮位_次数": 0, "档案_小桌_次数": 0,
            "抗拒状态": False, "抗拒_think_计数": 0, "抗拒_rest_计数": 0,
            "风险触发总次数": 0, "已完成场景": [],
            "已解锁_塑料布": False, "时间警告": False,
        }
        self.scenes = {
            "办公室": self.scene_office, "化学系": self.scene_lab,
            "工地": self.scene_construction, "电台": self.scene_radio,
            "档案": self.scene_archive,
        }
        self.npcs = {
            "佐伯教授": self.npc_professor, "三浦博士": self.npc_miura,
            "管理员": self.npc_manager, "DJ": self.npc_dj,
            "档案管理员": self.npc_archivist,
        }
        self.npc_locations = {
            "佐伯教授": "办公室", "三浦博士": "化学系",
            "管理员": "工地", "DJ": "电台", "档案管理员": "档案",
        }
        self.map_locations = {
            "办公室": "民俗学研究所 · 佐伯教授办公室",
            "化学系": "M大学 · 化学系 · 光谱分析实验室",
            "工地": "东京湾 · 东北角 · 填海工地",
            "电台": "旧楼 · 顶层 · 独立电台室",
            "档案": "中央图书馆 · 地下档案室",
        }

    # ==================== 工具 ====================
    def add_clue(self, name):
        if name not in self.clues:
            self.clues.append(name)

    def change_mind(self, delta):
        self.mind = max(0, min(100, self.mind + delta))
        if self.mind <= 0 and not self.over:
            self.trigger_bad_ending("你的心智在潮声的低语中彻底沉了下去。")

    # ==================== 核心指令入口 ====================
    def cmd(self, raw_input):
        parts = raw_input.strip().split()
        if not parts:
            return "请输入指令。输入 help 查看可用指令。"
        action = parts[0].lower()
        arg = " ".join(parts[1:]) if len(parts) > 1 else ""
        if self.over:
            if action == "new_game":
                self.__init__()
                return "【新游戏开始】你又一次站在佐伯教授的办公室里，窗外是绵延不断的梅雨。"
            return f"游戏已结束（{self.ending}）。输入 new_game 重新开始。"
        if action == "help":
            return ("可用指令：look / look [对象] · talk [人物] · go [地点] · map · "
                    "think · items · rest · status · choose [A/B/C]（终章解锁后）")
        if self.flags["抗拒状态"]:
            return self.handle_resistance(action, arg)
        if action == "look":
            return self.do_look(arg)
        if action == "talk":
            return self.do_talk(arg)
        if action == "go":
            return self.do_go(arg)
        if action == "map":
            return self.do_map()
        if action == "think":
            return self.do_think()
        if action == "items":
            return self.do_items()
        if action == "rest":
            return self.do_rest()
        if action == "status":
            return self.do_status()
        if action == "choose":
            return self.do_choose(arg.upper())
        return f"未知指令：{action}。输入 help 查看可用指令。"

    # ==================== 抗拒状态处理 ====================
    def handle_resistance(self, action, arg):
        if action == "think":
            self.flags["抗拒_think_计数"] += 1
            if self.flags["抗拒_think_计数"] >= 5:
                self.flags["抗拒状态"] = False
                self.flags["风险触发总次数"] += 1
                return "你睁开眼睛。窗外的雨还在下，但那种从肩胛骨之间升起的凉意已经退去了。你可以继续调查了——但你知道，有些东西已经留在你脑海里了。"
            return [
                "你站在窗边，努力把刚才看到的画面从脑海里驱赶出去。你告诉自己那只是巧合——但你知道那不是。",
                "你深吸一口气。潮水的气味……你明明在东京，却闻到了海潮的气味。",
                "你闭上眼睛，强迫自己把注意力拉回当下。你告诉自己：我是侦探。我选择来这里，是因为我想知道真相。",
                "你开始默数自己的呼吸。一、二、三……你感觉到自己的心跳在慢慢平复。",
            ][self.flags["抗拒_think_计数"] - 1]
        elif action == "rest":
            self.flags["抗拒_rest_计数"] += 1
            if self.flags["抗拒_rest_计数"] >= 3:
                self.flags["抗拒状态"] = False
                self.flags["风险触发总次数"] += 1
                return "你从窗边直起身来，喝了一口已经凉透的茶。那股不适感已经被压下去了——至少暂时如此。"
            return [
                "你靠在窗边，看着窗外的雨。你让自己什么都不要想。雨声盖过了所有杂念。",
                "你闭上眼睛，听着雨声。有那么一瞬间，你几乎忘记了刚才看到的一切。",
            ][self.flags["抗拒_rest_计数"] - 1]
        elif action == "items":
            return self.do_items()
        elif action == "status":
            return self.do_status()
        elif action == "look":
            return "你瞥了一眼那个方向——然后立刻移开了目光。你现在不想再看任何东西。"
        elif action == "go":
            return "你走到门口，手放在门把手上——但你没有按下去。你不想带着这种感觉去任何地方。"
        elif action == "talk":
            return "你张了张嘴，但那些话卡在喉咙里。你需要先整理好自己的思绪。"
        return "你现在不想做这个。"

    # ==================== 指令实现 ====================
    def do_look(self, arg):
        if not arg:
            return self.scenes[self.location]("look")
        return self.scenes[self.location](f"look {arg}")

    def do_talk(self, arg):
        if arg not in self.npcs:
            return f"没有叫 {arg} 的人在这里。"
        if self.npc_locations[arg] != self.location:
            return f"{arg}不在这里。她/他应该在【{self.map_locations[self.npc_locations[arg]]}】。"
        self.talk_rounds[arg] += 1
        return self.npcs[arg]()

    def do_go(self, arg):
        if arg not in self.map_locations:
            return "无法前往该地点。可用 map 查看可前往的地点。"
        if arg == self.location:
            return f"你已经在 {self.map_locations[arg]} 了。"
        self.location = arg
        self.time = min(100, self.time + 10)
        if arg not in self.flags["已完成场景"]:
            self.flags["已完成场景"].append(arg)
        extra = ""
        if self.time >= 100 and not self.flags["时间警告"]:
            self.flags["时间警告"] = True
            extra = ("\n\n你的手机响了。是佐伯教授：『时间不多了。那幅画今晚就要被转运。"
                     "你查到什么了？……回来吧，该做个了断了。』")
        return f"你来到了 {self.map_locations[arg]}。\n{self.scenes[arg]('look')}{extra}"

    def do_map(self):
        lines = ["【可前往的地点】"]
        for key, name in self.map_locations.items():
            mark = "（当前所在）" if key == self.location else ""
            lines.append(f"- {name} {mark}")
        return "\n".join(lines)

    def do_think(self):
        import random
        if self.flags["风险触发总次数"] > 0:
            fail_rate = 15 + (self.flags["风险触发总次数"] - 1) * 5
            if random.randint(1, 100) <= fail_rate:
                return "你思绪纷乱，无法集中精神。"
        lines = ["你整理了目前已知的线索："]
        mapping = {
            "教授初次接触": "- 【教授的初次接触】教授在1998年第一次看到那幅画的照片。",
            "实验室介绍信": "- 【实验室介绍信】佐伯教授让你去找三浦博士。",
            "封印的秘密": "- 【封印的秘密】那幅画出土的建筑是被海草和贝壳封死的。",
            "潮声采访记录": "- 【潮声采访记录】1998年9月12日，有人采访了咲岛幸存者。",
            "颜料分析报告": "- 【颜料分析报告】古画颜料中含有非地球已知物质，有『记忆』特性。",
            "三浦警告": "- 【三浦博士的警告】那种物质『不像是这个时代的东西』。",
            "三浦名片": "- 【三浦博士的名片】可以带新样本去找她。",
            "送魂结": "- 【送魂结的草绳】那幅画系着『送魂结』，被认为带有不祥之物。",
            "工地照片": "- 【工地现场照片】记录了古画出土的现场。",
            "建筑笔记": "- 【建筑结构笔记】建筑比江户时代更古老。",
            "潮声描述": "- 【『潮声』的描述】一个只在深夜出现的奇怪来电者。",
            "潮声录音": "- 【『潮声』的录音片段】『潮水之下，有声音。不是海的声音。是人的声音。』",
            "未完成词": "- 【未完成的词】『是……』——她没说完。",
            "纸条口述": "- 【纸条的口述记录】『潮水之下，有人来过。』",
            "笔记本来历": "- 【笔记本的来历】没人知道是谁留下的。",
            "潮位借阅": "- 【潮位记录本的借阅记录】1998年9月12日有人查阅过。",
            "教授工地回忆": "- 【教授的工地回忆】他当年去过那扇门。",
            "教授与三浦": "- 【教授与三浦的关联】『潮声』的声音是三浦博士的。",
            "教授坦白": "- 【教授的完整坦白】他承认那张纸条是他写的。",
            "抗拒状态": "- 【已触及：潮水之下】你在多个地点看到了『潮水之下』的意象。",
        }
        for k, v in mapping.items():
            if k in self.clues:
                lines.append(v)
        if len(lines) == 1:
            lines.append("（目前还没有任何线索。去调查吧。）")
        if "教授坦白" in self.clues:
            lines.append("\n—— 你已经触及全部真相。回到办公室，用 choose A/B/C 做出终章选择。")
        return "\n".join(lines)

    def do_items(self):
        return f"随身物品：{', '.join(self.items)}"

    def do_rest(self):
        self.change_mind(+10)
        self.time = min(100, self.time + 5)
        return f"你合上眼，听着窗外的雨声，小憩片刻。心智恢复 +10（当前：{self.mind}）。时间推进至 {self.time}%。"

    def do_status(self):
        return (f"【当前状态】\n📍 地点：{self.map_locations[self.location]}\n"
                f"🧠 心智：{self.mind}\n⏳ 时间进度：{self.time}%\n"
                f"📜 已获线索：{len(self.clues)} 条")

    # ==================== 场景定义 ====================
    def scene_office(self, action):
        if action == "look":
            return "办公室不大，一张老旧的木办公桌靠墙，桌面上摊着地图和文件。靠门一侧是顶天立地的书架，对面是一扇大窗户。空气里有旧纸页和湿木头的气味。佐伯教授站在窗前。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "书架":
                self.flags["办公室_书架_次数"] += 1
                if self.flags["办公室_书架_次数"] == 1:
                    return "书架上除了民俗学专著，还有一排书脊贴着『禁借』标签的旧书。"
                if self.flags["办公室_书架_次数"] == 2:
                    return "编号是连续的：D-07 到 D-13。第二层还放着一排旧录音带——也许值得凑近看看（look 书架第二层）。"
                return "没有更多可看的了。"
            if obj == "书架第二层":
                if self.flags["办公室_书架_次数"] < 1:
                    return "你还没仔细看过书架。"
                self.add_clue("潮声采访记录")
                return ("一排旧录音带，其中一卷标签写着：『1998.9.12 · 潮声采访·咲岛幸存者』。"
                        "背面有一行铅笔字：『幸存者自称「玄岳」。此人为咲岛最后一任神主。』\n"
                        "【获得线索：潮声采访记录】")
            if obj == "桌面":
                self.flags["办公室_桌面_次数"] += 1
                if self.flags["办公室_桌面_次数"] == 1:
                    return "摊开着一份东京湾潮位图，有几个日期被红笔圈了起来。"
                if self.flags["办公室_桌面_次数"] == 2:
                    return "6月3日、6月10日、6月14日（今天）。"
                return "没有更多可看的了。"
            if obj in ("地图", "红圈"):
                return "红圈位置在东京湾东北角，旁边有一行铅笔字：『此处为江户时代潮位观测所旧址』。"
            if obj == "窗台":
                return "窗台上有一层薄灰，但有一块区域是干净的，略呈弧形。"
            if obj in ("日光灯", "灯管"):
                return "日光灯管发出嗡嗡声，一端在闪烁，上方绑着一根极细的黑线。"
            if obj == "窗户":
                self.flags["办公室_窗户_次数"] += 1
                if self.flags["办公室_窗户_次数"] == 1:
                    return "窗玻璃上有水痕，还有几道笔直的线条。"
                if self.flags["办公室_窗户_次数"] == 2:
                    return "那是七芒星的一个角。"
                return self.trigger_resistance()
            if obj == "门背后":
                self.flags["办公室_门背后_次数"] += 1
                if self.flags["办公室_门背后_次数"] == 1:
                    return "挂着一件旧雨衣，雨衣下有一个木相框，面朝墙壁。"
                if self.flags["办公室_门背后_次数"] == 2:
                    return "相框里是教授和一个老人的合照，老人的脸被涂掉了。"
                return self.trigger_resistance()
            if obj == "垃圾桶":
                self.flags["办公室_垃圾桶_次数"] += 1
                if self.flags["办公室_垃圾桶_次数"] == 1:
                    return "有一团揉皱的纸，上面有潦草的字迹。"
                if self.flags["办公室_垃圾桶_次数"] == 2:
                    return "纸上写着：『不要看它的眼睛。不要问它的名字。不要回忆它的形状。』"
                return self.trigger_resistance()
            return f"没有什么特别的 {obj}。"
        return "你在办公室。可用指令：look, look [对象], talk 佐伯教授, go [地点]"

    def scene_lab(self, action):
        if action == "look":
            return "一间被仪器堆满的实验室。显微镜、样本架、电脑屏幕。三浦博士正从显微镜前抬起头来。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "显微镜":
                self.flags["化学_显微镜_次数"] += 1
                if self.flags["化学_显微镜_次数"] == 1:
                    return "一台老式显微镜，目镜旁贴着『三浦』的标签。"
                if self.flags["化学_显微镜_次数"] == 2:
                    return "目镜里残留着一小片干涸的暗红色样本。"
                return "没有更多可看的了。"
            if obj == "样本架":
                return "一支标签上写着『咲岛·古画·颜料』。"
            if obj == "电脑屏幕":
                return "光谱图有一条峰值，不在任何已知元素的范围内。"
            if obj == "窗台":
                self.flags["化学_窗台_次数"] += 1
                if self.flags["化学_窗台_次数"] == 1:
                    return "窗台上放着一盆枯萎的绿萝。"
                if self.flags["化学_窗台_次数"] == 2:
                    return "花盆底部有一圈白色的盐渍。"
                return self.trigger_resistance()
            return f"没有什么特别的 {obj}。"
        return "你在化学系实验室。可用指令：look, look [对象], talk 三浦博士, go [地点]"

    def scene_construction(self, action):
        if action == "look":
            return "挖掘机停在一旁，坑洞底部露出深色木结构。一个穿着雨衣的管理员站在旁边。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "坑洞":
                self.flags["工地_坑洞_次数"] += 1
                if self.flags["工地_坑洞_次数"] == 1:
                    return "木结构的切割方式不像江户时代。"
                if self.flags["工地_坑洞_次数"] == 2:
                    return "木料表面有『咲』字的残形。"
                return "没有更多可看的了。"
            if obj == "瓦片":
                self.flags["工地_瓦片_次数"] += 1
                if self.flags["工地_瓦片_次数"] == 1:
                    return "瓦片上刻着七芒星的一角。"
                if self.flags["工地_瓦片_次数"] == 2:
                    return "背面刻着『元禄十五年』（1702年）。"
                return "没有更多可看的了。"
            if obj == "塑料布":
                if not self.flags["已解锁_塑料布"]:
                    return "你需要先和管理员聊聊才能动这些东西。"
                return "木板内侧有字：『勿启此门』。笔迹和办公室垃圾桶里那张纸条，出自同一只手。"
            if obj == "围栏":
                self.flags["工地_围栏_次数"] += 1
                if self.flags["工地_围栏_次数"] == 1:
                    return "系着一条褪色的绳子，绳结很古老。"
                if self.flags["工地_围栏_次数"] == 2:
                    self.add_clue("送魂结")
                    return "绳结上绑着一枚夜光贝。管理员说过，这种结叫『送魂结』——用来送走的，不是用来留住的。\n【获得线索：送魂结的草绳】"
                return self.trigger_resistance()
            return f"没有什么特别的 {obj}。"
        return "你在工地。可用指令：look, look [对象], talk 管理员, go [地点]"

    def scene_radio(self, action):
        if action == "look":
            return "一台调音台、一堆线缆、一个正对着麦克风发呆的DJ。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "调音台":
                self.flags["电台_调音台_次数"] += 1
                if self.flags["电台_调音台_次数"] == 1:
                    return "推子上刻着一些字符。"
                if self.flags["电台_调音台_次数"] == 2:
                    return "那是缩写：『S.S.』。"
                return "没有更多可看的了。"
            if obj == "播放器":
                return "磁带标签：『潮声·最后一通』。也许该问问DJ能不能放一段。"
            if obj == "线缆":
                return "线缆拖在地上，延伸到墙角，接口处绑着一片干枯的海草。"
            if obj == "天线":
                self.flags["电台_天线_次数"] += 1
                if self.flags["电台_天线_次数"] == 1:
                    return "天线设备上有一些线缆拖出窗外。"
                if self.flags["电台_天线_次数"] == 2:
                    return "其中一根线缆的接口处绑着一片干枯的海草。"
                return self.trigger_resistance()
            return f"没有什么特别的 {obj}。"
        return "你在电台室。可用指令：look, look [对象], talk DJ, go [地点]"

    def scene_archive(self, action):
        if action == "look":
            return "地下档案室，一排排铁柜。档案管理员坐在角落里。"
        if action.startswith("look "):
            obj = action.split(" ", 1)[1]
            if obj == "档案柜":
                self.flags["档案_档案柜_次数"] += 1
                if self.flags["档案_档案柜_次数"] == 1:
                    return "『1998』的那格半开着。"
                if self.flags["档案_档案柜_次数"] == 2:
                    return "里面有一叠发黄的表格。"
                return "没有更多可看的了。"
            if obj == "潮位记录本":
                self.flags["档案_潮位_次数"] += 1
                if self.flags["档案_潮位_次数"] == 1:
                    return "1998年9月12日出现了异常尖峰。"
                if self.flags["档案_潮位_次数"] == 2:
                    return "页边写着：『潮』。"
                return "没有更多可看的了。"
            if obj == "小桌":
                self.flags["档案_小桌_次数"] += 1
                if self.flags["档案_小桌_次数"] == 1:
                    return "一盏老式台灯和一本翻开的笔记本。"
                if self.flags["档案_小桌_次数"] == 2:
                    return "笔记本上画着七芒星，旁边写着：『它还在。』"
                return self.trigger_resistance()
            return f"没有什么特别的 {obj}。"
        return "你在档案馆。可用指令：look, look [对象], talk 档案管理员, go [地点]"

    # ==================== 风险触发 ====================
    def trigger_resistance(self):
        self.flags["抗拒状态"] = True
        self.flags["抗拒_think_计数"] = 0
        self.flags["抗拒_rest_计数"] = 0
        self.add_clue("抗拒状态")
        self.change_mind(-15)
        if self.over:
            return self._bad_ending_text
        return (f"你盯着那行字，忽然感到一阵从肩胛骨之间升起的凉意。你不想再看下去了。你需要缓一缓。\n"
                f"心智 -15（当前：{self.mind}）\n（已进入抗拒状态。可用 think 5次 或 rest 3次 解除。）")

    # ==================== NPC 定义 ====================
    def npc_professor(self):
        r = self.talk_rounds["佐伯教授"]
        if r == 1:
            self.add_clue("教授初次接触")
            self.add_clue("实验室介绍信")
            return ("佐伯教授背对着你站着，没有回头。『你看到了什么？』\n"
                    "你说了窗户上的线条。他沉默了很久：『1998年，我第一次看到那幅画的照片。\n"
                    "我的导师……他是咲岛事件的调查者。9月12日之后，他失踪了。』\n"
                    "他递给你一封介绍信：『去化学系找三浦博士，让她看看颜料。』\n"
                    "【获得线索：教授的初次接触、实验室介绍信】")
        # 终章推进：按持有线索逐步解锁
        if "潮声录音" in self.clues and "教授与三浦" not in self.clues:
            self.add_clue("教授与三浦")
            return ("你把电台的录音放给教授听。他的脸色瞬间变得苍白。\n"
                    "『……那是三浦的声音。』他几乎是耳语，『二十多年前的三浦。\n"
                    "可1998年她还是个刚入行的研究员——她为什么要自称「潮声」，深夜给电台打电话？』\n"
                    "【获得线索：教授与三浦的关联】")
        if ("工地照片" in self.clues or "建筑笔记" in self.clues) and "教授工地回忆" not in self.clues:
            self.add_clue("教授工地回忆")
            return ("你把工地的照片推到他面前。教授的手抖了一下。\n"
                    "『……我去过那扇门。1998年，跟着导师。门缝里渗出来的不是水，是光。\n"
                    "导师把那张纸条塞进我手里，让我『永远不要回来』。』\n"
                    "【获得线索：教授的工地回忆】")
        if "教授与三浦" in self.clues and "潮位借阅" in self.clues and "教授坦白" not in self.clues:
            self.add_clue("教授坦白")
            return ("你把潮位记录本的借阅记录摊开：1998年9月12日，借阅人一栏是教授的签名。\n"
                    "他闭上眼睛，像放下了扛了二十八年的东西：\n"
                    "『是我写的纸条。「不要看它的眼睛。」我以为只要没人记得，它就会一直睡下去。\n"
                    "还有一件事……录音带里那个自称「玄岳」的幸存者。江户时代的档案里，\n"
                    "前任神主玄岳明明「享年六十有三」。相隔两百年，同一个名字。\n"
                    "要么记录是假的——要么，「玄岳」从来不是一个人，而是一个被传递下去的名字。』\n"
                    "【获得线索：教授的完整坦白】\n"
                    "（终章已解锁：用 choose A/B/C 做出你的选择。）")
        return "佐伯教授看着你，眼神里带着一丝疲惫。『还有什么发现吗？』"

    def npc_miura(self):
        r = self.talk_rounds["三浦博士"]
        if "实验室介绍信" not in self.clues:
            return "三浦博士从显微镜前抬起头来，锐利的目光看着你。『佐伯让你来的？口说无凭。』她转过身去。"
        if r == 1 or "颜料分析报告" not in self.clues:
            self.add_clue("颜料分析报告")
            return ("她看完介绍信，接过你描述的样本架编号，调出光谱图。\n"
                    "『古画颜料里有一种不在任何已知元素范围内的峰值。更奇怪的是——\n"
                    "它对观察者有反应。同一批样本，不同的人看，峰值会动。』\n"
                    "『这东西不是颜料。它有「记忆」的特性。』\n【获得线索：颜料分析报告】")
        if "三浦警告" not in self.clues:
            self.add_clue("三浦警告")
            return ("『我劝你停手。』她压低声音，『这种物质不像是这个时代的东西。\n"
                    "它不腐败、不分解，二十八年了，活性一点没降——像是在等什么。』\n【获得线索：三浦博士的警告】")
        if "三浦名片" not in self.clues:
            self.add_clue("三浦名片")
            return ("她递给你一张名片：『如果你找到新的样本……带回来给我。』\n"
                    "名片的纸质很旧了，边角磨圆——像是被人攥在手里很多年。\n"
                    "你注意到她办公室日历上，9月12日被红笔圈了一个小小的圈。\n【获得线索：三浦博士的名片】")
        return "三浦博士重新埋回显微镜前：『有样本再来。』"

    def npc_manager(self):
        r = self.talk_rounds["管理员"]
        if r == 1:
            self.add_clue("封印的秘密")
            self.flags["已解锁_塑料布"] = True
            return ("管理员指着坑洞：『那幅画是在一扇门下面找到的。我们没敢动那扇门。\n"
                    "门缝全被海草和贝壳封死了——从里面封的。像是谁把什么东西锁在底下，又怕它出来。』\n"
                    "他忽然压低声音：『你们调查可以，别撬门。塑料布下面的木板……你自己去看吧。』\n"
                    "【获得线索：封印的秘密】（塑料布已解锁）")
        if "工地照片" not in self.clues:
            self.add_clue("工地照片")
            return ("他翻出一叠现场照片：『出土那天拍的。你看这张——画框上的绳子，\n"
                    "老工人说那叫「送魂结」，是给死人引路用的，系反了方向。\n"
                    "像是故意不让魂走，又故意不让魂留。』\n【获得线索：工地现场照片】")
        if "建筑笔记" not in self.clues:
            self.add_clue("建筑笔记")
            return ("『结构师傅看了木料，说切割方式比江户还老。瓦片背后刻着「元禄十五年」。\n"
                    "1702年啊。这底下的东西，比这座城埋得都深。』\n【获得线索：建筑结构笔记】")
        return "管理员裹紧雨衣：『别撬门。』"

    def npc_dj(self):
        r = self.talk_rounds["DJ"]
        if r == 1:
            self.add_clue("潮声描述")
            return ("DJ摘下耳机：『佐伯教授的学生？他说过你可能来。\n"
                    "「潮声」啊……一个只在深夜打进来的来电者，从不报名字，只说海的事。\n"
                    "1998年9月之后，再也没来过电话。』\n【获得线索：『潮声』的描述】")
        if "潮声录音" not in self.clues:
            self.add_clue("潮声录音")
            return ("『最后一通我还留着。』他按下播放键。磁带沙沙作响，一个年轻女人的声音：\n"
                    "『潮水之下，有声音。不是海的声音。是人的声音。它们记得所有被忘掉的事——\n"
                    "如果你们看到了那扇门，不要……』录音在这里断了一秒。\n【获得线索：『潮声』的录音片段】")
        if "未完成词" not in self.clues:
            self.add_clue("未完成词")
            return ("『断掉的那一秒，我后来单独听过几百遍。』DJ说，『她最后说了半个字。\n"
                    "『是……』——然后就挂了。她到底想说『是什么』？我猜了二十八年。』\n"
                    "【获得线索：未完成的词】")
        return "DJ把耳机戴回去：『潮声没再打来过。』"

    def npc_archivist(self):
        r = self.talk_rounds["档案管理员"]
        if r == 1:
            self.add_clue("纸条口述")
            return ("档案管理员推了推眼镜：『1998年的潮位记录？最里面那排铁柜。\n"
                    "对了，那年还收过一张奇怪的纸条，口述记录写的是——\n"
                    "『潮水之下，有人来过。』没有署名。』\n【获得线索：纸条的口述记录】")
        if "笔记本来历" not in self.clues:
            self.add_clue("笔记本来历")
            return ("『小桌上那本笔记？没人知道是谁留下的。1998年9月12日那天晚上，\n"
                    "它就在那儿了，翻开的那页画着七芒星。我们不敢扔，也不敢收进编目。』\n"
                    "【获得线索：笔记本的来历】")
        if "潮位借阅" not in self.clues:
            self.add_clue("潮位借阅")
            return ("『借阅记录？』她抽出一本发黄的登记册，『1998年9月12日，\n"
                    "潮位记录本只有一个人借过。签名是……佐伯。你们研究所的那位教授。』\n"
                    "【获得线索：潮位记录本的借阅记录】")
        return "档案管理员重新看起书来。"

    # ==================== 终章：结局 ====================
    def do_choose(self, arg):
        if "教授坦白" not in self.clues:
            return "还没有到做选择的时候——你还没有拼出完整的真相。（继续调查，找佐伯教授谈谈。）"
        if arg not in ("A", "B", "C"):
            return ("终章选择：\n"
                    "  choose A —— 当作没看见。离开东京，把一切留在身后。\n"
                    "  choose B —— 毁掉它。把那幅画、那盘磁带、所有证据付之一炬。\n"
                    "  choose C —— 直面潮声。听完那盘录音，找到「潮声」本人。")
        if arg == "A":
            self.over = True
            self.ending = "坏结局 · 被潮水吞没"
            return ("【坏结局 · 被潮水吞没】\n你选择了离开。你告诉自己那只是巧合，只是疲惫，只是梅雨季节的错觉。\n"
                    "但从那以后，每当下雨，你都会听见潮声。东京没有海——可潮声越来越近。\n"
                    "三个月后的一个深夜，你在自己的窗户玻璃上，看到了七芒星的一个角。\n"
                    "（你没有成为解谜的人。你成为了谜的一部分。）")
        if arg == "B":
            self.over = True
            self.ending = "普通结局 · 封印的记忆"
            return ("【普通结局 · 封印的记忆】\n你把画、磁带、笔记本全部烧掉了。火光里，你仿佛听见一声叹息——\n"
                    "不是愤怒，是疲惫。教授没有阻拦你，他只是在火光前站了很久。\n"
                    "秘密被埋了回去，就像1998年那次一样。潮声停了。\n"
                    "但你知道，它只是又睡着了。它记得你——就像它记得每一个见过它的人。\n"
                    "（封印完成。代价是：没有人再知道门下面有什么。）")
        # choose C
        if "潮声录音" in self.clues and "三浦名片" in self.clues:
            self.over = True
            self.ending = "好结局 · 潮声的回响"
            return ("【好结局 · 潮声的回响】\n你带着录音带和那张被攥了多年的名片，走进化学系的实验室。\n"
                    "你按下播放键：『潮水之下，有声音。』\n"
                    "三浦博士的手停在半空。二十八年的沉默碎了。\n"
                    "『……是我。』她说。那个深夜来电的「潮声」，那个没说完的『是……』——『是我。』\n"
                    "1998年，她是第一个看到光谱异常的研究生；她打电话去电台，是想警告所有人。\n"
                    "『门下面的东西，靠「被遗忘」活着。只要还有人记得潮声，它就不算赢。』\n"
                    "你问她那个自称玄岳的幸存者是谁。她摇头：『那不是一个人。那是一个名字——\n"
                    "一个被潮水带了两百年的名字。』\n"
                    "你合上笔记本。案子没有结束，但你终于知道自己面对的是什么。\n"
                    "（真相结局 · 现代篇完。第三章：那扇没有打开的门。）")
        return ("你握住播放键，却停住了——你还缺最后一块拼图。\n"
                "直面潮声需要两样东西：【『潮声』的录音片段】和【三浦博士的名片】。再回去找找。")

    def trigger_bad_ending(self, reason):
        self.over = True
        self.ending = "坏结局 · 被潮水吞没"
        self._bad_ending_text = (f"【坏结局 · 被潮水吞没】\n{reason}\n"
                                 "你在东京的梅雨季里听见了海。你的影子开始不听使唤，\n"
                                 "你的记忆里混进了不属于你的画面——两百年前，一座岛，一扇门。\n"
                                 "（输入 new_game 重新开始。）")
        return self._bad_ending_text


# ==================== 模块级入口 ====================
_game = SakiGameChapter2()

def cmd(command):
    """统一指令入口：import 之后直接 cmd('look') 即可游玩。"""
    return _game.cmd(command)

def new_game():
    """开新局。"""
    return _game.cmd("new_game")

# ==================== 命令行入口 ====================
if __name__ == "__main__":
    print("《咲神变奏曲》· 第二章：东京湾回声")
    print("类型：文字推理游戏。输入 help 查看指令。")
    print("你站在佐伯教授的办公室里，窗外是绵延不断的梅雨。")
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
