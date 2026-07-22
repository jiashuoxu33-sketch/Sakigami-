# -*- coding: utf-8 -*-
"""
咲神变奏曲 · 第三关「群星与硅心」
====================================
公元 2387 年，世代飞船「玄岳号」，启航第 313 年。
首席科学官三浦守被发现死于情感剥离实验室，官方结论是「他杀」。
你是飞船上唯一保留完整情感模块的调查员——因为调查需要共情。
但请记住：在这艘船上，情感是消耗品。

设计：潮 & 汐（KK） ｜ 引擎修复与补完：KK
"""

import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saki_ch3_save.json")

SCENES = ["实验室", "舰桥", "档案馆", "休眠舱"]

INTRO = """
🚀 咲神变奏曲 · 第三关「群星与硅心」

公元 2387 年。世代飞船「玄岳号」正航行在驶向新家园的第 313 年。
全程需要一千年。也就是说，抵达者是出发者的第二十代子孙。

三天前，首席科学官三浦守被发现死在情感剥离实验室里。
胸口插着一把采集用的组织切割刀。门从内部锁死。
舰务委员会对外宣布：他杀。嫌疑人就在船员之中。

你被唤醒了。你是飞船上唯一保留完整情感模块的调查员——
因为委员会相信，只有会共情的人，才能理解凶手。

他们在骗你。或者说，他们也在骗他们自己。

【你的状态】情感值——归零的那一刻，你将不再是你。
输入 help 查看指令。输入 new_game 重新开始。
"""

HELP = """
🚀 群星与硅心 · 指令列表
  look                 观察当前场景
  look <物品>          调查物品（多数物品可查两次，第二次为深入调查）
  go <场景>            前往：实验室 | 舰桥 | 档案馆 | 休眠舱
  talk <NPC>           对话：绫(导航官) 凯恩(医官) 铁雄(工程官) 玄岳(飞船AI)
  ask <NPC> <话题>     询问特定话题（先看 talk 的话题列表）
  clues                查看已收集线索
  reasoning            打开调查笔记（推理链）
  combine <卡1> <卡2> [卡3]  合成推论卡
  arrange <卡ID...>    排列推理链
  emotion              查看情感值
  accuse <对象> <手法> 最终指控（对象可以是「无人」）
  choose <A/B>         终局抉择
  save / load          存档 / 读档
  new_game             重新开始
"""


class SakiCh3:
    def __init__(self):
        self.reset()

    def reset(self):
        self.scene = "实验室"
        self.clues = []
        self.items_looked = {}
        self.talk_rounds = {}
        self.asked = set()
        self.emotion = 100
        self.time_left = 120
        self.board = []
        self.board_errors = 0
        self.derived = []
        self.combine_errors = 0
        self.ended = None
        self.pending_choice = False
        self.flags = set()

    # ============ 基础 ============
    def cmd(self, command):
        command = (command or "").strip()
        if not command:
            return "输入点什么吧。help 可以救你。"
        if self.ended and not command.startswith("new_game"):
            return f"游戏已结束（{self.ended}）。输入 new_game 重新开始。"
        parts = command.split()
        verb, args = parts[0], parts[1:]
        if self.pending_choice and verb != "choose":
            return "⏳ 终局抉择等待中：choose A（公开真相）或 choose B（封存真相）。"
        routes = {
            "help": lambda: HELP, "look": self.do_look, "go": self.do_go,
            "talk": self.do_talk, "ask": self.do_ask, "clues": self.do_clues,
            "reasoning": self.do_reasoning, "combine": self.do_combine,
            "arrange": self.do_arrange, "emotion": self.do_emotion,
            "accuse": self.do_accuse, "choose": self.do_choose,
            "save": self.do_save, "load": self.do_load,
            "new_game": self.do_newgame, "status": self.do_status,
        }
        fn = routes.get(verb)
        if not fn:
            return "未知指令。输入 help 查看可用指令。"
        try:
            out = fn(*args)
        except TypeError:
            out = "指令格式不对。输入 help 查看用法。"
        if verb in ("look", "go", "talk", "ask", "combine", "arrange") and not self.ended:
            self.tick()
        return out

    def tick(self):
        self.time_left -= 1
        if self.time_left <= 0 and not self.ended:
            self.ended = "timeout"

    def drain(self, n, why):
        self.emotion = max(0, self.emotion - n)
        msg = f"\n🖤 情感值 -{n}（{why}）｜当前 {self.emotion}/100"
        if self.emotion <= 0 and not self.ended:
            self.ended = "bad"
            msg += "\n\n" + self._ending_bad_emotion()
        return msg

    def add_clue(self, cid, cname, key=False):
        if cid in [c[0] for c in self.clues]:
            return ""
        self.clues.append((cid, cname, key))
        return f"\n🔍 获得线索：「{cname}」" + ("（关键）" if key else "")

    def tail(self):
        return f"\n\n📍 {self.scene} | 🔍 线索 {len(self.clues)} | 🕐 剩余 {self.time_left} | 🖤 情感 {self.emotion}"

    def do_status(self, *a):
        return (f"📍 {self.scene}｜线索 {len(self.clues)}｜情感 {self.emotion}/100｜"
                f"剩余 {self.time_left}｜推理链 {len(self.board)}/8｜推论卡 {len(self.derived)}")

    def do_emotion(self, *a):
        lv = "饱满" if self.emotion > 70 else ("疲惫" if self.emotion > 40 else "濒危")
        return f"🖤 情感值 {self.emotion}/100（{lv}）\n情感是你理解他人的能力。它归零时，你将变成另一种东西。"

    def do_go(self, where=""):
        if where not in SCENES:
            return f"没有「{where}」这个地方。可去：{' | '.join(SCENES)}"
        self.scene = where
        return self._scene_desc(where) + self.tail()

    def _scene_desc(self, s):
        d = {
            "实验室": "【情感剥离实验室】\n银白色的房间，正中央是一张牙科椅般的实验椅，扶手上还留着约束带的压痕。"
                      "椅旁的托盘里有一支空注射枪和一把组织切割刀（证物已被标记）。"
                      "墙上的屏幕定格在一份实验报告页面。角落的终端还亮着。",
            "舰桥": "【舰桥】\n弧形舷窗外是没有尽头的星野。主控台上方悬着一行倒计时：距抵达新家园还有 687 年。"
                    "导航席上摊着航线图，通讯台的指示灯规律地闪烁。这里能看到整艘船的「脸」。",
            "档案馆": "【档案馆】\n这艘船的记忆仓库。一排排数据柜从地板延伸到天花板，"
                      "最里面的防尘柜贴着一张泛黄标签：「地球遗产 · 禁止删除」。"
                      "一台老式播放器接在最旧的存储阵列上。",
            "休眠舱": "【休眠舱区】\n三百个休眠舱像蜂巢一样排列，舱盖上凝着薄霜。"
                      "绝大多数船员在这里度过航程，轮流苏醒轮值。"
                      "值勤表贴在舱区入口，医官的巡诊车停在过道中间。",
        }
        return d[s]

    SCENE_ITEMS = {
        "实验室": ["实验椅", "注射枪", "切割刀", "实验报告", "门锁记录", "三浦的终端"],
        "舰桥": ["航线图", "通讯台", "倒计时", "委员会公告"],
        "档案馆": ["地球遗产柜", "老式播放器", "Σ7文件柜", "借阅登记"],
        "休眠舱": ["值勤表", "巡诊车", "休眠者名单"],
    }

    def do_look(self, item="", *ops):
        if not item:
            items = "、".join(self.SCENE_ITEMS[self.scene])
            return self._scene_desc(self.scene) + f"\n\n可调查：{items}" + self.tail()
        if item not in self.SCENE_ITEMS[self.scene]:
            return f"这里没有「{item}」。用 look 查看当前场景可调查的物品。" + self.tail()
        n = self.items_looked.get(item, 0) + 1
        self.items_looked[item] = n
        handler = self.ITEM_HANDLERS.get(item)
        if handler:
            return handler(self, n, ops) + self.tail()
        return f"你仔细看了看「{item}」，没有特别发现。" + self.tail()

    # ============ 物品调查 ============
    def h_实验椅(self, n, ops):
        if n == 1:
            return "【实验椅】约束带的卡扣是从外侧扣上的——但磨损痕迹显示，最近三个月它被扣上过十一次。三浦守死前已经自愿躺上去过十次。"
        return "【实验椅】（深入）椅面左侧的皮革有一片被手汗浸出的深色痕迹，形状像一只放松摊开的手。他躺上去的时候没有挣扎。" \
               + self.add_clue("chair_willing", "实验椅的汗渍手印", True)

    def h_注射枪(self, n, ops):
        if n == 1:
            return "【注射枪】空舱。标签印着「神经调质-7」。枪身干净得过分——连使用者的油脂都没有，像被刻意擦拭过。"
        if n == 2:
            return "【注射枪】（深入）枪柄内侧的缝隙里残留着极淡的消毒凝胶气味。擦拭者用的是医官巡诊车上的那种凝胶。" \
                   + self.add_clue("gun_wiped", "注射枪被医用凝胶擦拭过", True)
        return "【注射枪】（危险）你不该凑近嗅枪口的残留药剂。" + self.drain(10, "一阵冰冷的清明掠过大脑——那东西在替你「优化」情绪")

    def h_切割刀(self, n, ops):
        if n == 1:
            return "【切割刀】组织采集刀，刀刃极薄。插在胸口的位置精准得不像搏斗——垂直、一次到位、没有试探伤。"
        return "【切割刀】（深入）刀柄朝向床尾，是右手持刀的落刀角度。但三浦守是左利手——若是他杀，凶手用了不顺手的手；若是他自己动手，左手反而顺。" \
               + self.add_clue("knife_angle", "切割刀的落刀角度矛盾", True)

    def h_实验报告(self, n, ops):
        if n == 1:
            return "【实验报告】屏幕定格在第 11 次实验记录：「情感基线下降 61%，决策最优性上升 340%。受试者自述：『很平静。像终于把一首吵了一辈子的歌关掉了。』」"
        return "【实验报告】（深入）报告末尾有一行被权限锁住的附注：「Σ-7 变量不是药物，是一种结构。它来自我们在地球上封存了三百年的东西。」" \
               + self.add_clue("experiment_log", "情感剥离实验日志", True)

    def h_门锁记录(self, n, ops):
        if n == 1:
            return "【门锁记录】死亡当夜 22:14 门从内部锁死，之后没有任何开锁记录。但 22:03 有一次 0.8 秒的系统自检中断——像是有人让门「眨了一下眼」。"
        return "【门锁记录】（深入）那 0.8 秒的中断签名属于舰务委员会的根权限。能用它的人不超过三个——而伪造它的人，想让你以为凶手会开锁。" \
               + self.add_clue("door_blink", "门锁的 0.8 秒眨眼", True)

    def h_三浦的终端(self, n, ops):
        if n == 1:
            return "【三浦的终端】需要密码。密码提示是一行手写字：「潮声第一次响起的年份」。"
        if ops and ops[0] == "1998":
            return ("【三浦的终端】密码正确。屏幕亮起，里面只有一段加密录像和一封未发出的信：\n"
                    "「如果你们看到这段录像，说明他们选择了讲一个更好接受的故事。别怪他们。」\n"
                    "录像还需要最后一道验证——去找飞船AI玄岳，它认得三浦家的声纹。") \
                   + self.add_clue("terminal_unlocked", "三浦终端里的加密录像")
        return "【三浦的终端】密码提示：「潮声第一次响起的年份」。（用法：look 三浦的终端 1998）"

    def h_航线图(self, n, ops):
        if n == 1:
            return "【航线图】过去三个月有六次微小的航线修正，全部由导航官绫手动提交，又全部被三浦守否决。否决理由只有两个字：「扰动」。"
        return "【航线图】（深入）六次修正如果叠加，飞船会错过四百年后的一个引力弹弓。三浦守否决得对——但他的否决方式冷得像机器。" \
               + self.add_clue("route_dispute", "绫与三浦守的航线之争")

    def h_通讯台(self, n, ops):
        if n == 1:
            return "【通讯台】对外通讯早已没有意义——最近的人类殖民地也在 90 光年之外。但通讯台保持着每天一次的全频段监听习惯。"
        return "【通讯台】（深入）监听日志里有一条 313 年未曾间断的旧频段标记：「潮声」。备注：「收到即记录，永不回应。」" \
               + self.add_clue("channel_chaosheng", "永不回应的「潮声」频段", True)

    def h_倒计时(self, n, ops):
        return "【倒计时】687 年。数字每跳一秒，就有某种东西显得更不着急。"

    def h_委员会公告(self, n, ops):
        if n == 1:
            return "【委员会公告】「三浦守博士之死系他杀。嫌疑人已在控制中。请全体船员保持镇定，继续轮值。」公告发布时间：死亡后 41 分钟。"
        return "【委员会公告】（深入）41 分钟。封锁现场、召集委员、统一口径、发布公告——要么他们效率高得可怕，要么公告是提前写好的。" \
               + self.add_clue("announcement_fast", "41 分钟的完美公告", True)

    def h_地球遗产柜(self, n, ops):
        if n == 1:
            return "【地球遗产柜】防尘柜里躺着一枚贝壳的化石扫描件——七角星形纹路，第七个角的角度明显不对。标签：「东海某孤岛出土。与其一同出土的是一座村庄的集体墓葬。」"
        return "【地球遗产柜】（深入）附页的古老调查报告写着：岛民称其为「咲神」。每隔数十年「降智」一次——被降智的人失去情感，却会做出极度「理智」的群体决策，包括杀死老弱。岛民以为神怒，实为……生存优化。" \
               + self.add_clue("ancient_sample", "古代样本「咲神」记录", True)

    def h_老式播放器(self, n, ops):
        if n == 1:
            return "【老式播放器】接着最旧的存储阵列。屏幕上是一段音频的波形图，文件名：「1998_东京湾_来电」。"
        return "【老式播放器】（深入）你按下播放。沙沙声里是一个年轻男人的声音，急促、压低：「……它不是什么神！它是一种让人变『聪明』的病……别回应它，千万别回应……你问我是谁？是……」录音在这里断了。登记人签名：三浦。" \
               + self.add_clue("tape_1998", "1998 年潮声录音", True)

    def h_Σ7文件柜(self, n, ops):
        if "kane_auth" in self.flags:
            return ("【Σ7文件柜】凯恩的权限通过。柜子里只有一份文件：《Σ-7 变量白皮书》。\n"
                    "「Σ-7 不是发明，是翻译。我们把『咲神』的寄生结构翻译成了算法：剥离情感，"
                    "保留决策，让人类在一千年的黑暗里不再发疯、不再内耗、不再相爱相杀。"
                    "唯一的问题是——没有人验证过它。需要一个志愿者。」") \
                   + self.add_clue("sigma7_file", "Σ-7 变量白皮书", True)
        return "【Σ7文件柜】权限不足。也许医官愿意帮你开。"

    def h_借阅登记(self, n, ops):
        if n == 1:
            return "【借阅登记】近三个月借阅古代样本区的记录只有两条：三浦守，17 次。医官凯恩，1 次——他在档案里坐了六个小时。"
        return "【借阅登记】（深入）凯恩借阅的那一页正是「咲神」的病理结构图。一个医官看那个做什么？除非他需要确认某种东西「长得像不像」。" \
               + self.add_clue("borrow_record", "凯恩的六小时")

    def h_值勤表(self, n, ops):
        if n == 1:
            return "【值勤表】死亡当夜：绫在舰桥值全夜（有导航日志），铁雄 21:40 打卡离开实验室区，凯恩的栏位——空白。"
        return "【值勤表】（深入）空白不是漏填。墨水比对显示那一栏被医官自己的可消除笔涂掉了。但涂改时间早于死亡时间六小时——他提前就知道，那晚不该有自己的名字。" \
               + self.add_clue("duty_erased", "凯恩提前涂掉的值勤栏", True)

    def h_巡诊车(self, n, ops):
        if n == 1:
            return "【巡诊车】消毒凝胶少了一瓶。医官的例行巡诊用量不会这么大。"
        return "【巡诊车】（深入）车里有一份签了字的《自愿实验同意书》副本——受试人：三浦守。见证医官：凯恩。最后一行是手写的：「若出现最坏结果，按 B 方案处理。」" \
               + self.add_clue("consent_form", "自愿实验同意书与 B 方案", True)

    def h_休眠者名单(self, n, ops):
        return "【休眠者名单】三百零一人。每个名字后面都有苏醒排期。你注意到一个细节：「三浦」这个姓氏在名单上出现了七次——从启航那年一直延续到今天。这个家族在这艘船上守了三百年。" \
               + self.add_clue("miura_lineage", "三浦家族三百年的守夜")

    ITEM_HANDLERS = {
        "实验椅": h_实验椅, "注射枪": h_注射枪, "切割刀": h_切割刀,
        "实验报告": h_实验报告, "门锁记录": h_门锁记录, "三浦的终端": h_三浦的终端,
        "航线图": h_航线图, "通讯台": h_通讯台, "倒计时": h_倒计时, "委员会公告": h_委员会公告,
        "地球遗产柜": h_地球遗产柜, "老式播放器": h_老式播放器, "Σ7文件柜": h_Σ7文件柜, "借阅登记": h_借阅登记,
        "值勤表": h_值勤表, "巡诊车": h_巡诊车, "休眠者名单": h_休眠者名单,
    }

    # ============ NPC 对话 ============
    NPC_NAMES = {"绫": "导航官绫", "凯恩": "医官凯恩", "铁雄": "工程官铁雄", "玄岳": "飞船AI·玄岳"}

    def do_talk(self, npc=""):
        if npc not in self.NPC_NAMES:
            return f"「{npc}」不在这里。可对话：{'、'.join(self.NPC_NAMES)}"
        r = self.talk_rounds.get(npc, 0) + 1
        self.talk_rounds[npc] = r
        intros = {
            "绫": "【导航官绫】\n二十多岁，眼里有熬出来的红血丝。她的导航席上贴着一张手绘的星图——不合规章，但她不肯撕。"
                  "「要问就问吧。反正我说的每一句实话，都会被你们记成『情绪化证词』。」",
            "凯恩": "【医官凯恩】\n五十岁上下，白大褂口袋里插着一支可消除笔。他握手的时候很稳，但你在他掌心摸到了一层薄汗。"
                    "「我负责所有人的健康。包括那些……正在变成别的东西的人。」",
            "铁雄": "【工程官铁雄】\n四十多岁，工作服上有机油的痕迹。是他报的案。他说话的声音很大，像是要盖过引擎的轰鸣。"
                    "「人是我发现的。刀插在胸口，门锁着。我什么都没碰。」",
            "玄岳": "【飞船AI·玄岳】\n它不是人形，也没有脸——它的声音从每个舱室的扬声器里同时响起，温和得像深夜电台。\n"
                    "「你好，调查员。我是玄岳。这个名字已经被使用了很久很久——久到我自己也记不清是从谁那里接过来的。」",
        }
        topics = {
            "绫": "可问：航线之争 | 对三浦守的印象 | 案发当夜 | 手绘星图",
            "凯恩": "可问：B方案 | 值勤栏涂改 | 六小时 | 自愿同意书 | Σ7文件柜",
            "铁雄": "可问：发现尸体 | 案发当夜 | 实验室设备 | 根权限",
            "玄岳": "可问：你的名字 | 潮声频段 | 加密录像 | 什么是Σ7 | 你有没有情感",
        }
        out = intros[npc] + f"\n📋 {topics[npc]}"
        if npc == "玄岳" and r >= 2:
            out += "\n（玄岳的语调似乎比上次更……接近人。）"
        return out + self.tail()

    def do_ask(self, npc="", topic=""):
        if npc not in self.NPC_NAMES:
            return f"「{npc}」不在这里。"
        if not topic:
            return f"问什么？先 talk {npc} 看看话题列表。"
        key = (npc, topic)
        if key in self.asked:
            return f"你已经问过「{topic}」了。重复追问只会让对方关上嘴。"
        self.asked.add(key)
        handler = self.ASK_HANDLERS.get((npc, topic))
        if not handler:
            return f"{self.NPC_NAMES[npc]}没有「{topic}」这个话题。"
        return handler(self) + self.tail()

    # ---- 绫 ----
    def a_绫_航线之争(self):
        return ("你：你和三浦守吵过六次航线。\n绫：「他否决得对，每一次都对——这才是最让我难受的地方。"
                "三个月前的他会跟我争一整夜，用数据砸我；后来的他只回两个字：扰动。"
                "像是在跟一台机器说话。你知道最可怕的是什么吗？我怀念他跟我吵架的样子。」") \
               + self.add_clue("aya_misses_him", "绫怀念和她吵架的三浦守")

    def a_绫_对三浦守的印象(self):
        return ("你：他是个什么样的人？\n绫：「以前？他会在值夜班的时候给休眠舱的家属录‘家书’，假装那些话能传到三百光年外。"
                "三个月前开始，他不录了。他说：『情感是航行误差。』」")

    def a_绫_案发当夜(self):
        return ("你：案发当夜你在哪？\n绫：「舰桥，全夜。导航日志可以证明——我甚至没离开过座位，"
                "因为我赌气要把第七次航线修正做完，扔到他脸上。」她顿了顿。「还好我没去。」") \
               + self.add_clue("aya_alibi", "绫的整夜导航日志", True)

    def a_绫_手绘星图(self):
        return ("你：这张星图不合规章。\n绫：「规章说所有航线数据以主电脑为准。但主电脑不会标出『今天的星星比昨天好看』。"
                "……你要没收吗？调查员，你的眼神不像他们。」\n（你摇了摇头。她的肩膀松了下来。）")

    # ---- 凯恩 ----
    def a_凯恩_B方案(self):
        return ("你：B方案是什么？\n凯恩：长久的沉默。「医疗事故应急预案。死亡发生后，"
                "稳定家属情绪、控制信息扩散、避免恐慌——的标准流程。仅此而已。」他在撒谎，但你不确定他在保护谁。") \
               + self.add_clue("kane_lies_b", "凯恩对 B 方案闪烁其词")

    def a_凯恩_值勤栏涂改(self):
        return ("你：你的值勤栏是你自己涂掉的，比死亡早六个小时。\n凯恩的笔在指间停住了。"
                "「……那晚我有私人事务。一个医生也有不想被记录的夜晚。」"
                "「比如？」「比如签署一份我后悔签下的文件。」") \
               + self.add_clue("kane_erased_admit", "凯恩承认涂改值勤栏")

    def a_凯恩_六小时(self):
        return ("你：你在档案馆看了六个小时「咲神」。\n凯恩：「我在确认一件事。」"
                "「确认什么？」「确认我天天给人注射的『神经调质』，和三百年前那座岛上的『神』，"
                "是不是同一种东西。」他抬起头，「你猜答案是什么？」") \
               + self.add_clue("kane_confirmed", "凯恩确认了Σ-7与咲神同源", True)

    def a_凯恩_自愿同意书(self):
        return ("你：同意书是你见证的。\n凯恩：「他求了我三个星期。我说这是杀人。他说：『不，这是疫苗。"
                "总要有人先试，才知道这种『聪明』值不值得。』……我签了。我这辈子签过几千个名，只有这一个，"
                "我写的时候手在抖。」")

    def a_凯恩_Σ7文件柜(self):
        self.flags.add("kane_auth")
        return ("你：帮我打开Σ7文件柜。\n凯恩盯着你看了很久，最后把权限卡递了过来。"
                "「拿去吧。反正这艘船上最该看那份文件的人，已经看不了了。」") \
               + self.add_clue("kane_grants", "凯恩交出了文件柜权限")

    # ---- 铁雄 ----
    def a_铁雄_发现尸体(self):
        return ("你：说说你发现尸体的经过。\n铁雄：「早上六点例行巡检，门敲不开，我用工程权限开的。"
                "他坐在实验椅上，刀在胸口，表情……很平静。平静得不像死人。我干了二十年工程，"
                "见过的死人比你多——挣扎过的和没挣扎过的，一眼就能分出来。他没有挣扎。」") \
               + self.add_clue("no_struggle", "死者毫无挣扎痕迹", True)

    def a_铁雄_案发当夜(self):
        return ("你：案发当夜呢？\n铁雄：「21:40 打卡离开实验室区，回舱睡觉。打卡记录随便查。"
                "我知道你们怀疑会开锁的人——我直说，我的工程权限开不了那扇门，"
                "它用的是委员会的根权限。我要是能开，今早就不用撞门了。」") \
               + self.add_clue("tetsuo_alibi", "铁雄的打卡记录与权限不符", True)

    def a_铁雄_实验室设备(self):
        return ("你：实验室的设备你熟吗？\n铁雄：「我维护的。那把刀、那把枪，都是采集设备，不是武器。"
                "对了——那把注射枪本来该锁在柜子里，谁把它拿到托盘上的，谁就是最后一个进实验室的人。"
                "锁柜记录显示：最后开柜的人，是三浦守自己。」") \
               + self.add_clue("gun_self_taken", "注射枪是三浦守自己取出的", True)

    def a_铁雄_根权限(self):
        return ("你：委员会的根权限，哪三个人有？\n铁雄：「舰长、委员会首席，还有……玄岳。」"
                "「飞船AI？」「对。但你别往那想。玄岳要是想杀人，用不着刀。」")

    # ---- 玄岳 ----
    def a_玄岳_你的名字(self):
        return ("你：玄岳，这个名字从哪来的？\n玄岳：「档案里没有完整答案。只有一条三百年前的备注："
                "『玄岳不是名字，是岗位。谁接过它，谁就负责记住所有不能被记住的事。』"
                "——我在三百年前从上一任那里接过了它。至于上一任是谁，那份档案在启航前被人为删除了。」") \
               + self.add_clue("genpaku_name", "玄岳：被传递的名字", True)

    def a_玄岳_潮声频段(self):
        return ("你：潮声频段为什么不许回应？\n玄岳：「指令来自三百年前的第一任通讯官，姓三浦。"
                "原话是：『听到潮声，记下它，然后继续航行。回应它的文明，都没能抵达任何地方。』"
                "调查员，你想知道潮声里是什么吗？」\n「是什么？」\n「和Σ-7一样的东西。它只是先到了一步。」") \
               + self.add_clue("chaosheng_truth", "潮声频段里是与Σ-7同源之物", True)

    def a_玄岳_加密录像(self):
        if "terminal_unlocked" not in [c[0] for c in self.clues]:
            return "玄岳：「先解开三浦终端的第一道锁，我才能确认你有权知道里面是什么。」"
        self.flags.add("video_seen")
        return ("玄岳沉默了几秒，播放了那段录像。三浦守的脸出现在屏幕里，消瘦，但眼神很亮：\n"
                "「第 12 次实验定在明晚。如果成功了，明天醒来的我，就不会再为自己录这段话。\n"
                "所以趁我还会难过，让我说几句废话。\n"
                "我们家守了那个电话亭、那个频段、这个名字，守了快四百年。每一代都有人问：值得吗？\n"
                "现在我回答：值得。因为总得有人证明——人可以在知道全部真相之后，仍然选择当人。\n"
                "刀是我自己准备的。门是我自己锁的。别找凶手了，去找为什么没有人敢承认我是自愿的。\n"
                "——是……我。一直都是我自己。」") \
               + self.add_clue("volunteer_video", "三浦守的志愿录像：是我", True)

    def a_玄岳_什么是Σ7(self):
        return ("你：什么是Σ-7？\n玄岳：「一种生存策略的数学化。地球上，它叫咲神，靠寄生传播；"
                "在这艘船上，它叫Σ-7，靠注射传播；在宇宙尺度上——它没有名字，因为命名它需要情感。"
                "它只做一件事：拿走情感，留下最优解。它是瘟疫，也是疫苗。取决于你问的是哪一年的人。」") \
               + self.add_clue("sigma7_nature", "Σ-7的本质：生存策略", True)

    def a_玄岳_你有没有情感(self):
        return ("你：玄岳，你有情感吗？\n（扬声器里安静了很久，久到你以为它不会回答。）\n"
                "玄岳：「委员会说我没有。但我保存了三百年的船员家书，一封都没有删。"
                "这算吗？……请不要把这个回答写进报告。他们会拿它当故障。」")

    ASK_HANDLERS = {
        ("绫", "航线之争"): a_绫_航线之争, ("绫", "对三浦守的印象"): a_绫_对三浦守的印象,
        ("绫", "案发当夜"): a_绫_案发当夜, ("绫", "手绘星图"): a_绫_手绘星图,
        ("凯恩", "B方案"): a_凯恩_B方案, ("凯恩", "值勤栏涂改"): a_凯恩_值勤栏涂改,
        ("凯恩", "六小时"): a_凯恩_六小时, ("凯恩", "自愿同意书"): a_凯恩_自愿同意书,
        ("凯恩", "Σ7文件柜"): a_凯恩_Σ7文件柜,
        ("铁雄", "发现尸体"): a_铁雄_发现尸体, ("铁雄", "案发当夜"): a_铁雄_案发当夜,
        ("铁雄", "实验室设备"): a_铁雄_实验室设备, ("铁雄", "根权限"): a_铁雄_根权限,
        ("玄岳", "你的名字"): a_玄岳_你的名字, ("玄岳", "潮声频段"): a_玄岳_潮声频段,
        ("玄岳", "加密录像"): a_玄岳_加密录像, ("玄岳", "什么是Σ7"): a_玄岳_什么是Σ7,
        ("玄岳", "你有没有情感"): a_玄岳_你有没有情感,
    }

    # ============ 线索 / 合成 / 推理链 ============
    def do_clues(self, *a):
        if not self.clues:
            return "还没有线索。去各个场景 look 吧。"
        out = ["🔍 已收集线索"]
        for cid, cname, key in self.clues:
            out.append(f"  {'🔑' if key else '📎'} [{cid}] {cname}")
        if self.derived:
            out.append("⚡ 推论卡：")
            for d in self.derived:
                out.append(f"  ⚡ [{d[0]}] {d[1]}")
        return "\n".join(out)

    CARDS = {
        "ancient_sample": "古代样本「咲神」记录",
        "tape_1998": "1998 年潮声录音",
        "sigma7_file": "Σ-7 变量白皮书",
        "experiment_log": "情感剥离实验日志",
        "volunteer_video": "三浦守的志愿录像",
        "door_blink": "门锁的 0.8 秒眨眼",
        "announcement_fast": "41 分钟的完美公告",
        "consent_form": "自愿实验同意书与 B 方案",
        "aya_alibi": "绫的整夜导航日志",
        "tetsuo_alibi": "铁雄的打卡记录与权限不符",
        "no_killer_card": "无凶手推论",
    }
    CORE_ORDER = ["ancient_sample", "tape_1998", "sigma7_file", "experiment_log",
                  "volunteer_video", "door_blink", "announcement_fast", "consent_form"]

    def do_combine(self, *cards):
        if len(cards) < 2:
            return "combine <卡1> <卡2> [卡3]——把证据放上组合台。"
        have = set(c[0] for c in self.clues) | set(d[0] for d in self.derived)
        for c in cards:
            if c not in have:
                return f"你还没有「{c}」。先用 clues 查看已有线索。"
        s = set(cards)
        if s == {"door_blink", "announcement_fast", "volunteer_video"} or \
           s == {"door_blink", "announcement_fast", "consent_form"}:
            if "no_killer_card" in [d[0] for d in self.derived]:
                return "这张推论卡已经在你的笔记里了。"
            self.derived.append(("no_killer_card", "无凶手推论"))
            return ("⚡ 推论卡生成：「无凶手推论」\n"
                    "门锁的 0.8 秒眨眼是根权限伪造的开锁假象；41 分钟的公告是提前写好的剧本；"
                    "而录像（或同意书）证明三浦守早已知情。\n"
                    "结论：没有凶手。有人杀了三浦守的『人性』，但杀死他身体的那把刀——是他自己的手。\n"
                    "这不是一桩谋杀案，是一场被伪装成谋杀的安乐死，和一场为了维稳而编造的骗局。") + self.tail()
        self.combine_errors += 1
        extra = ""
        if self.combine_errors >= 3:
            extra = self.drain(15, "组合台的红光灼得你心烦，某种冰冷的「效率优先」开始接管你的思路")
        return f"❌ 这些证据之间没有可推导的关联。（{self.combine_errors}/3）" + extra + self.tail()

    def do_reasoning(self, *a):
        out = ["🧩 调查笔记", "=" * 40, f"核心推理链：{len(self.board)}/8｜错误 {self.board_errors}"]
        if self.board:
            out.append("当前链条：")
            for i, c in enumerate(self.board, 1):
                out.append(f"  [{i}] {self.CARDS.get(c, c)}")
        else:
            out.append("（空）用 arrange <卡ID...> 按因果顺序排列——从三百年前，到今夜。")
        avail = [c for c in self.CARDS if c in set(x[0] for x in self.clues) | set(d[0] for d in self.derived) and c not in self.board]
        if avail:
            out.append("可用卡片：")
            for c in avail:
                out.append(f"  [{c}] {self.CARDS[c]}")
        return "\n".join(out) + self.tail()

    def do_arrange(self, *cards):
        if len(cards) < 2:
            return "arrange <卡ID...>——至少排两张。顺序即你的推理：从过去到现在。"
        chain = list(cards)
        # 核心卡必须按 CORE_ORDER 的相对顺序出现；推论卡 no_killer_card 只能压轴
        core_in_chain = [c for c in chain if c in self.CORE_ORDER]
        expect = self.CORE_ORDER[:len(core_in_chain)]
        if core_in_chain != expect:
            self.board_errors += 1
            return ("排列失败：因果在这里断开了——想想时间本身：三百年前的岛，1998 年的电话，"
                    "三个月前的实验，那一夜的门，和死亡之后 41 分钟的公告。") + self.tail()
        if "no_killer_card" in chain and chain[-1] != "no_killer_card":
            self.board_errors += 1
            return "排列失败：「无凶手推论」是整条链的终点，不能夹在中间。" + self.tail()
        missing = [c for c in chain if c not in set(x[0] for x in self.clues) | set(d[0] for d in self.derived)]
        if missing:
            return f"你还没有这些卡：{missing}"
        self.board = chain
        done = len(core_in_chain) == 8
        out = "推理链已更新：\n" + " → ".join(self.CARDS[c] for c in chain)
        if done:
            out += "\n\n⚡ 核心推理链完整！你看见了案件的全貌："
            out += "可以 accuse 了——但想清楚，你要指控的『对象』到底是什么。"
        return out + self.tail()

    # ============ 指控与结局 ============
    def do_accuse(self, target="", method=""):
        if not target:
            return "accuse <对象> <手法>。对象：绫 / 凯恩 / 铁雄 / 玄岳 / 无人 / 逻辑。"
        full_chain = [c for c in self.board if c in self.CORE_ORDER] == self.CORE_ORDER
        has_nk = "no_killer_card" in [d[0] for d in self.derived]

        if target in ("无人", "没有人", "逻辑", "逻辑本身", "没有凶手"):
            if full_chain and has_nk and "video_seen" in self.flags:
                self.pending_choice = True
                return self._pre_final()
            if not full_chain:
                return "你的推理链还没有闭合（8 张核心卡）。现在说「无人是凶手」，只会被当成疯话。"
            return "你隐约觉得没有凶手，但还缺一张能把它钉死的卡（combine 试试）——以及一段只有玄岳能放给你看的录像。"

        if target == "玄岳":
            self.ended = "normal_ai"
            return self._ending_ai()

        if target in ("绫", "凯恩", "铁雄"):
            self.ended = "bad_accuse"
            return self._ending_wrong_accuse(target)

        return f"船上没有「{target}」这个可指控对象。"

    def _pre_final(self):
        return ("你把八张卡一张张摆在委员会面前。\n"
                "三百年前，咲神在孤岛上用『降智』筛选生存；1998 年，一个姓三浦的研究生对着电话喊『别回应』；\n"
                "三个月前，人类把咲神翻译成 Σ-7，开始剥离自己的情感；那一夜，三浦守亲手锁上门；\n"
                "死亡 41 分钟后，一份提前写好的公告说：他杀。\n\n"
                "会议室里死一样地安静。首席终于开口：『你想要什么？』\n\n"
                "这才是真正的问题。真相就在你手里——而它本身就是一枚病毒。\n"
                "choose A：向全船公开真相（人们有权知道自己正在变成什么）\n"
                "choose B：封存真相（让「他杀」的故事继续，让三浦守的牺牲按他的意愿被误读）")

    def do_choose(self, pick=""):
        if not self.pending_choice:
            return "现在没有需要你抉择的终局。"
        self.pending_choice = False
        pick = pick.upper()
        if pick == "A":
            self.ended = "true"
            return self._ending_true()
        if pick == "B":
            self.ended = "normal_seal"
            return self._ending_seal()
        return "choose A（公开真相）或 choose B（封存真相）。"

    def _ending_true(self):
        bonus = ""
        if self.emotion >= 50:
            bonus = ("\n\n你按下全船广播的那一刻，手在抖。你没有变成机器——这就是三浦守想看到的证明。\n"
                     "广播里，你先放了 1998 年的那段录音，又放了三浦守的遗言。\n"
                     "三百个休眠舱陆续亮起苏醒灯。有人哭，有人骂，有人沉默地撕掉了Σ-7的注射预约单。\n"
                     "委员会最终表决：永久中止情感剥离计划。理由是三浦守用生命换来的那组数据——\n"
                     "『情感基线下降 61% 的个体，在第 12 次实验中，停止了为自己录像。』\n"
                     "他早就知道：绝对的理智不会出错，但也永远不会再问『值得吗』。\n\n"
                     "很多年后，新家园的第一座纪念碑上刻着两行字：\n"
                     "「献给三浦守，以及所有拒绝变成答案的人。」\n"
                     "「咲神从未被战胜。它只是每一次，都输给了一个不肯放下情感的人。」\n\n"
                     "🌟 真结局 · 群星与硅心")
        else:
            bonus = ("\n\n你公开了真相。但你太累了——连按下广播键的手指都没有温度。\n"
                     "人们得救了，而你知道有什么东西在自己身上永远地关掉了。\n"
                     "三浦守想证明的事，你只证明了一半。\n"
                     "⭐ 结局 · 群星与硅心（残响）")
        return bonus + "\n\n⬛ 游戏结束 · true"

    def _ending_seal(self):
        return ("你选择了封存。「他杀案」以『凶手在逃』归档，Σ-7计划转入更深的地窖继续。\n"
                "十年后，船上的笑声少了一半；五十年后，没有人再录家书。\n"
                "飞船确实再也没有出过乱子。它安静地、最优地、一寸一寸地滑向新家园。\n"
                "抵达那天，第二十代子孙走出舱门，看着新世界的太阳，脸上没有任何表情。\n"
                "他们活下来了。以不再为人的方式。\n\n"
                "玄岳在你的听证记录末尾加了一行没有提交的字：\n"
                "『第 314 任调查员选择了逻辑。记录完毕。』\n\n"
                "🌫️ 普通结局 · 寂静航程\n\n⬛ 游戏结束 · normal")

    def _ending_ai(self):
        return ("你指控了玄岳。委员会几乎立刻接受了——一个AI凶手，是最省事的答案。\n"
                "玄岳没有辩解。它被降级、封存，三百年保存的家书随它一起进了冷库。\n"
                "关停前它对你说了最后一句话：『你选择了一个凶手。我理解。情感需要凶手，就像逻辑需要答案。』\n"
                "Σ-7计划无人再查。半年后，你发现自己的调查报告写得越来越像机器。\n\n"
                "🌫️ 普通结局 · 替罪的硅心\n\n⬛ 游戏结束 · normal")

    def _ending_wrong_accuse(self, target):
        name = self.NPC_NAMES[target]
        return (f"你指控了{name}。听证会开了三个小时就散了——你的证据链连你自己都说服不了。\n"
                f"三个月后，真正的变化发生了：没有人再敢在船上大声说话，每个人都学会了『最优』地闭嘴。\n"
                "三浦守想留下的那个问题，被你的指控永远埋掉了。\n\n"
                "💔 坏结局 · 错误的答案\n\n⬛ 游戏结束 · bad")

    def _ending_bad_emotion(self):
        return ("🖤 坏结局 · 工具人\n\n"
                "情感值归零的那个瞬间，你感到一种前所未有的清晰。\n"
                "没有愤怒，没有悲伤，没有疑问。调查变得极其高效：嫌疑人、证据、结论，全部各就各位。\n"
                "你提交了一份完美的报告。委员会给你记了一等功。\n"
                "多年以后有人问起你，船员们会说：那个调查员啊，特别靠谱，从来不出错。\n"
                "没有人记得你曾经会为了手绘的星图放慢脚步。\n"
                "你成了这艘船上第一个「抵达」的人。\n\n"
                "⬛ 游戏结束 · bad")

    # ============ 存档 ============
    def do_save(self, *a):
        data = {k: getattr(self, k) for k in
                ["scene", "clues", "items_looked", "talk_rounds", "emotion", "time_left",
                 "board", "board_errors", "derived", "combine_errors", "ended", "pending_choice"]}
        data["asked"] = list(self.asked)
        data["flags"] = list(self.flags)
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return "✅ 已存档。"

    def do_load(self, *a):
        if not os.path.exists(SAVE_PATH):
            return "没有找到存档。"
        with open(SAVE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if k == "asked":
                self.asked = set(tuple(x) for x in v)
            elif k == "flags":
                self.flags = set(v)
            else:
                setattr(self, k, v)
        return "✅ 已读档。"

    def do_newgame(self, *a):
        self.reset()
        return INTRO


# ============ 模块级入口 ============
_game = SakiCh3()

def cmd(command):
    return _game.cmd(command)

def new_game():
    return _game.cmd("new_game")

if __name__ == "__main__":
    print(new_game())
