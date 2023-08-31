import time

from bot.base.task import TaskStatus, EndTaskReason
from module.umamusume.asset.point import *
from module.umamusume.context import TurnInfo
from module.umamusume.script.cultivate_task.const import SKILL_LEARN_PRIORITY_LIST
from module.umamusume.script.cultivate_task.event import get_event_choice
from module.umamusume.script.cultivate_task.parse import *

log = logger.get_logger(__name__)


def script_cultivate_main_menu(ctx: UmamusumeContext):
    img = ctx.current_screen
    current_date = parse_date(img, ctx)
    if current_date == -1:
        log.warning("解析日期失败")
        return
    # 如果进入新的一回合，记录旧的回合信息并创建新的
    if ctx.cultivate_detail.turn_info is None or current_date != ctx.cultivate_detail.turn_info.date:
        if ctx.cultivate_detail.turn_info is not None:
            ctx.cultivate_detail.turn_info_history.append(ctx.cultivate_detail.turn_info)
        ctx.cultivate_detail.turn_info = TurnInfo()
        ctx.cultivate_detail.turn_info.date = current_date

    # 解析主界面
    if not ctx.cultivate_detail.turn_info.parse_main_menu_finish:
        parse_cultivate_main_menu(ctx, img)
        return

    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
        ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
        return

    turn_operation = ctx.cultivate_detail.turn_info.turn_operation
    if turn_operation is not None:
        if turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRAINING:
            ctx.ctrl.click_by_point(TO_TRAINING_SELECT)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_REST:
            ctx.ctrl.click_by_point(CULTIVATE_REST)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_MEDIC:
            if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                ctx.ctrl.click_by_point(CULTIVATE_MEDIC_SUMMER)
            else:
                ctx.ctrl.click_by_point(CULTIVATE_MEDIC)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_TRIP:
            ctx.ctrl.click_by_point(CULTIVATE_TRIP)
        elif turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
            if 36 < ctx.cultivate_detail.turn_info.date <= 40 or 60 < ctx.cultivate_detail.turn_info.date <= 64:
                ctx.ctrl.click_by_point(CULTIVATE_RACE_SUMMER)
            else:
                ctx.ctrl.click_by_point(CULTIVATE_RACE)


def script_cultivate_training_select(ctx: UmamusumeContext):
    if ctx.cultivate_detail.turn_info is None:
        log.warning("回合信息未初始化")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return

    if ctx.cultivate_detail.turn_info.turn_operation is not None:
        if (ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type ==
                TurnOperationType.TURN_OPERATION_TYPE_TRAINING):
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[ctx.cultivate_detail.turn_info.turn_operation.training_type.value - 1])
            time.sleep(0.5)
            ctx.ctrl.click_by_point(
                TRAINING_POINT_LIST[ctx.cultivate_detail.turn_info.turn_operation.training_type.value - 1])
            time.sleep(3)
            return
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
            return

    if not ctx.cultivate_detail.turn_info.parse_train_info_finish:
        img = ctx.ctrl.get_screen()
        train_type = parse_train_type(ctx, img)
        if train_type == TrainingType.TRAINING_TYPE_UNKNOWN:
            return
        parse_training_result(ctx, img, train_type)
        parse_training_support_card(ctx, img, train_type)
        viewed = train_type.value
        for i in range(5):
            if i != (viewed - 1):
                retry = 0
                max_retry = 3
                img = ctx.ctrl.get_screen()
                while parse_train_type(ctx, img) != TrainingType(i + 1) and retry < max_retry:
                    ctx.ctrl.click_by_point(TRAINING_POINT_LIST[i])
                    time.sleep(0.3)
                    img = ctx.ctrl.get_screen()
                    retry += 1
                if retry == max_retry:
                    return
                parse_training_result(ctx, img, TrainingType(i + 1))
                parse_training_support_card(ctx, img, TrainingType(i + 1))
        ctx.cultivate_detail.turn_info.parse_train_info_finish = True


def script_main_menu(ctx: UmamusumeContext):
    if ctx.cultivate_detail.cultivate_finish:
        ctx.task.end_task(TaskStatus.TASK_STATUS_SUCCESS, EndTaskReason.COMPLETE)
        return
    ctx.ctrl.click_by_point(TO_CULTIVATE_SCENARIO_CHOOSE)


def script_scenario_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_umamusume_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_extend_umamusume_select(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_support_card_select(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen(to_gray=True)
    if image_match(img, REF_CULTIVATE_SUPPORT_CARD_EMPTY).find_match:
        ctx.ctrl.click_by_point(TO_FOLLOW_SUPPORT_CARD_SELECT)
    ctx.ctrl.click_by_point(TO_CULTIVATE_PREPARE_NEXT)


def script_follow_support_card_select(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen()
    while True:
        selected = find_support_card(ctx, img)
        if selected:
            break
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if np.all(img[1096, 693] == [125, 120, 142]):
            ctx.ctrl.click_by_point(FOLLOW_SUPPORT_CARD_SELECT_REFRESH)
            break
        ctx.ctrl.swipe(x1=350, y1=1000, x2=350, y2=400, duration=1000, name="")
        time.sleep(1)
        img = ctx.ctrl.get_screen()


def script_cultivate_final_check(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_FINAL_CHECK_START)


def script_cultivate_event(ctx: UmamusumeContext):
    img = ctx.ctrl.get_screen()
    event_name, selector_list = parse_cultivate_event(ctx, img)
    log.debug("当前事件：%s", event_name)
    if len(selector_list) != 0:
        choice_index = get_event_choice(event_name)
        ctx.ctrl.click(selector_list[choice_index - 1][0], selector_list[choice_index - 1][1],
                       "事件选项-" + str(choice_index))
    else:
        log.debug("未出现选项")


def script_cultivate_goal_race(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_1)


def script_cultivate_race_list(ctx: UmamusumeContext):
    if ctx.cultivate_detail.turn_info is None:
        log.warning("回合信息未初始化")
        ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
        return
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2GRAY)
    if image_match(img, REF_RACE_LIST_GOAL_RACE).find_match:
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)
    elif image_match(img, REF_RACE_LIST_URA_RACE).find_match:
        ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)
    else:
        if ctx.cultivate_detail.turn_info.turn_operation is None:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)
            return
        if ctx.cultivate_detail.turn_info.turn_operation.turn_operation_type == TurnOperationType.TURN_OPERATION_TYPE_RACE:
            img = ctx.current_screen
            while True:
                selected = find_race(ctx, img, ctx.cultivate_detail.turn_info.turn_operation.race_id)
                if selected:
                    time.sleep(1)
                    ctx.ctrl.click_by_point(CULTIVATE_GOAL_RACE_INTER_2)
                    time.sleep(1)
                    return
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                if np.all(img[1006, 701] != [211, 209, 219]):
                    break
                ctx.ctrl.swipe(x1=23, y1=1000, x2=23, y2=850, duration=1000, name="")
                time.sleep(1)
                img = ctx.ctrl.get_screen()
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_MAIN_MENU)

# 575 745
def script_cultivate_before_race(ctx: UmamusumeContext):
    img = cv2.cvtColor(ctx.current_screen, cv2.COLOR_BGR2RGB)
    p_check_skip = img[1175, 330]
    p_check_tactic_1 = img[668, 480]
    p_check_tactic_2 = img[668, 542]
    p_check_tactic_3 = img[668, 600]
    p_check_tactic_4 = img[668, 670]

    if p_check_tactic_4[0] < 200 and p_check_tactic_4[1] < 200 and p_check_tactic_4[2] < 200:
        ctx.ctrl.click_by_point(BEFORE_RACE_CHANGE_TACTIC)

    if p_check_skip[0] < 200 and p_check_skip[1] < 200 and p_check_skip[2] < 200:
        ctx.ctrl.click_by_point(BEFORE_RACE_START)
    else:
        ctx.ctrl.click_by_point(BEFORE_RACE_SKIP)


def script_cultivate_in_race_uma_list(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(IN_RACE_UMA_LIST_CONFIRM)


def script_in_race(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(IN_RACE_SKIP)


def script_cultivate_race_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(RACE_RESULT_CONFIRM)


def script_cultivate_race_reward(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(RACE_REWARD_CONFIRM)


def script_cultivate_goal_achieved(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(GOAL_ACHIEVE_CONFIRM)


def script_cultivate_goal_failed(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(GOAL_FAIL_CONFIRM)

def script_cultivate_next_goal(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(NEXT_GOAL_CONFIRM)


def script_cultivate_extend(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_EXTEND_CONFIRM)


def script_cultivate_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_RESULT_CONFIRM)


def script_cultivate_catch_doll(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_CATCH_DOLL_START)


def script_cultivate_catch_doll_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_CATCH_DOLL_RESULT_CONFIRM)


def script_cultivate_finish(ctx: UmamusumeContext):
    if ctx.cultivate_detail.learn_skill_done:
        ctx.ctrl.click_by_point(CULTIVATE_FINISH_CONFIRM)
        ctx.cultivate_detail.cultivate_finish = True
    else:
        ctx.ctrl.click_by_point(CULTIVATE_FINISH_LEARN_SKILL)


def script_cultivate_learn_skill(ctx: UmamusumeContext):
    if ctx.cultivate_detail.learn_skill_done:
        if ctx.cultivate_detail.learn_skill_selected:
            ctx.ctrl.click_by_point(CULTIVATE_LEARN_SKILL_CONFIRM)
        else:
            ctx.ctrl.click_by_point(RETURN_TO_CULTIVATE_FINISH)
        return
    img = ctx.current_screen
    learn_skill_list: list
    if len(ctx.cultivate_detail.learn_skill_list) == 0:
        learn_skill_list = SKILL_LEARN_PRIORITY_LIST
    else:
        learn_skill_list = [ctx.cultivate_detail.learn_skill_list] + SKILL_LEARN_PRIORITY_LIST
    for i in range(len(learn_skill_list)):
        while True:
            find_skill(ctx, img, learn_skill_list[i], learn_any_skill=False)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if np.all(img[1006, 701] != [211, 209, 219]):
                break
            ctx.ctrl.swipe(x1=23, y1=1000, x2=23, y2=660, duration=1000, name="")
            time.sleep(1)
            img = ctx.ctrl.get_screen()
        while True:
            ctx.ctrl.swipe(x1=23, y1=620, x2=23, y2=1000, duration=200, name="")
            img = cv2.cvtColor(ctx.ctrl.get_screen(), cv2.COLOR_BGR2RGB)
            if np.all(img[488, 701] != [211, 209, 219]):
                time.sleep(1.5)
                break
    time.sleep(1)
    img = ctx.ctrl.get_screen()
    while True:
        find_skill(ctx, img, [], learn_any_skill=True)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if np.all(img[1006, 701] != [211, 209, 219]):
            break
        ctx.ctrl.swipe(x1=23, y1=1000, x2=23, y2=640, duration=1000, name="")
        time.sleep(1)
        img = ctx.ctrl.get_screen()
    ctx.cultivate_detail.learn_skill_done = True


def script_not_found_ui(ctx: UmamusumeContext):
    ctx.ctrl.click(719, 1, "")


def script_receive_cup(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_RECEIVE_CUP_CLOSE)


def script_cultivate_level_result(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_LEVEL_RESULT_CONFIRM)


def script_factor_receive(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(CULTIVATE_FACTOR_RECEIVE_CONFIRM)


def script_historical_rating_update(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(HISTORICAL_RATING_UPDATE_CONFIRM)


def script_scenario_rating_update(ctx: UmamusumeContext):
    ctx.ctrl.click_by_point(SCENARIO_RATING_UPDATE_CONFIRM)
