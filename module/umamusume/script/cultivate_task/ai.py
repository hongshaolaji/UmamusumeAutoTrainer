from module.umamusume.context import *
from module.umamusume.script.cultivate_task.support_card import get_support_card_score
import numpy as np

log = logger.get_logger(__name__)


def get_operation(ctx: UmamusumeContext) -> TurnOperation | None:

    turn_operation = TurnOperation()

    attribute_result = get_training_basic_attribute_score(ctx.cultivate_detail.turn_info,
                                                          ctx.cultivate_detail.expect_attribute)
    support_card_result = get_training_support_card_score(ctx)
    training_level_result = get_training_level_score(ctx)

    attribute_result_max = np.max(attribute_result)
    attribute_result_min = np.min(attribute_result)
    normalized_attribute_result = (attribute_result - attribute_result_min) / (
            attribute_result_max - attribute_result_min)

    support_card_max = np.max(support_card_result)
    support_card_min = np.min(support_card_result)
    if support_card_max != support_card_min:
        normalized_support_card_result = (support_card_result - support_card_min) / (
                support_card_max - support_card_min)
    else:
        normalized_support_card_result = [1, 1, 1, 1, 1]

    training_level_max = np.max(training_level_result)
    training_level_min = np.min(training_level_result)
    if training_level_min != training_level_max:
        normalized_training_level_result = (training_level_result - training_level_min) / (
                training_level_max - training_level_min)
    else:
        normalized_training_level_result = [1, 1, 1, 1, 1]

    # 第一年至第二年合宿前
    if ctx.cultivate_detail.turn_info.date <= 36:
        attr_weight = 0.2
        support_card_weight = 0.6
        training_level_weight = 0.2
    # 第二年合宿期间
    elif 36 < ctx.cultivate_detail.turn_info.date <= 40:
        attr_weight = 0.8
        support_card_weight = 0.2
        training_level_weight = 0
    # 第二年合宿后至第三年前
    elif 40 < ctx.cultivate_detail.turn_info.date <= 48:
        attr_weight = 0.4
        support_card_weight = 0.3
        training_level_weight = 0.3
    # 第三年合宿前
    elif 48 < ctx.cultivate_detail.turn_info.date <= 60:
        attr_weight = 0.4
        support_card_weight = 0.3
        training_level_weight = 0.3
    # 第三年合宿期间
    elif 60 < ctx.cultivate_detail.turn_info.date <= 64:
        attr_weight = 1
        support_card_weight = 0
        training_level_weight = 0
    # 第三年至结束
    elif 64 < ctx.cultivate_detail.turn_info.date <= 99:
        attr_weight = 0.7
        support_card_weight = 0.2
        training_level_weight = 0.1
    else:
        attr_weight = 1
        support_card_weight = 0
        training_level_weight = 0

    # 训练得分
    training_score = []
    for i in range(5):
        training_score.append(normalized_attribute_result[i] * attr_weight + normalized_support_card_result[i] *
                              support_card_weight + normalized_training_level_result[i] * training_level_weight)
    log.debug("训练综合得分：" + str(training_score))

    # 参加比赛
    extra_race_this_turn = [i for i in ctx.cultivate_detail.extra_race_list if str(i)[:2]
                            == str(ctx.cultivate_detail.turn_info.date)]
    if len(extra_race_this_turn) != 0:
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_RACE
        turn_operation.race_id = extra_race_this_turn[0]
        return turn_operation

    medic = False
    if ctx.cultivate_detail.turn_info.medic_room_available and ctx.cultivate_detail.turn_info.remain_stamina <= 60:
        medic = True

    trip = False
    if ctx.cultivate_detail.turn_info.date <= 36 and ctx.cultivate_detail.turn_info.motivation_level.value <= 3 and ctx.cultivate_detail.turn_info.remain_stamina < 90 \
            or 40 < ctx.cultivate_detail.turn_info.date <= 60 and ctx.cultivate_detail.turn_info.motivation_level.value <= 4 and ctx.cultivate_detail.turn_info.remain_stamina < 90\
            or 64 < ctx.cultivate_detail.turn_info.date <= 99 and ctx.cultivate_detail.turn_info.motivation_level.value <= 4 and ctx.cultivate_detail.turn_info.remain_stamina < 90:
        trip = True

    rest = False
    if ctx.cultivate_detail.turn_info.remain_stamina <= 40:
        rest = True
    elif (ctx.cultivate_detail.turn_info.date == 36 or ctx.cultivate_detail.turn_info.date == 60) and ctx.cultivate_detail.turn_info.remain_stamina < 65:
        rest = True
    elif np.max(training_score) - np.average(training_score) < 0.1 and ctx.cultivate_detail.turn_info.remain_stamina < 50:
        rest = True

    if medic:
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_MEDIC
        return turn_operation

    if trip:
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRIP
        return turn_operation

    if rest:
        turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_REST
        return turn_operation

    turn_operation.turn_operation_type = TurnOperationType.TURN_OPERATION_TYPE_TRAINING
    turn_operation.training_type = TrainingType(training_score.index(np.max(training_score))+1)

    return turn_operation


def get_training_level_score(ctx: UmamusumeContext):
    expect_attribute = ctx.cultivate_detail.expect_attribute
    total_score = 2
    result = []
    for i in range(len(expect_attribute)):
        result.append(expect_attribute[i] / sum(expect_attribute) * total_score)
    log.debug("每个训练设施的得分：" + str(result))
    return result


def get_training_support_card_score(ctx: UmamusumeContext) -> list[float]:
    turn_info = ctx.cultivate_detail.turn_info
    result = []
    for i in range(len(turn_info.training_info_list)):
        score = 0
        for j in range(len(turn_info.training_info_list[i].support_card_info_list)):
            score += get_support_card_score(ctx, turn_info.training_info_list[i].support_card_info_list[j])
        result.append(score)
    log.debug("每个训练的支援卡得分：" + str(result))
    return result


def get_training_basic_attribute_score(turn_info: TurnInfo, expect_attribute: list[int]) -> list[float]:
    origin = [turn_info.uma_attribute.speed, turn_info.uma_attribute.stamina, turn_info.uma_attribute.power,
              turn_info.uma_attribute.will, turn_info.uma_attribute.intelligence]
    result = []
    for i in range(len(turn_info.training_info_list)):
        incr = [turn_info.training_info_list[i].speed_incr, turn_info.training_info_list[i].stamina_incr,
                turn_info.training_info_list[i].power_incr, turn_info.training_info_list[i].will_incr,
                turn_info.training_info_list[i].intelligence_incr]
        rating_incr = 0
        for j in range(len(incr)):
            if incr[j] != 0:
                rating_incr += get_basic_status_score(incr[j] + origin[j]) - get_basic_status_score(origin[j])
        rating_incr += turn_info.training_info_list[i].skill_point_incr * 1.45
        result.append(rating_incr)
    log.debug("每个训练的属性增长得分：" + str(result))

    target_percent = [0, 0, 0, 0, 0]
    for i in range(len(origin)):
        target_percent[i] = origin[i] / expect_attribute[i]
    avg = sum(target_percent) / len(target_percent)
    for i in range(len(result)):
        result[i] = result[i] * (1 - (target_percent[i] - avg))
    log.debug("每个训练的属性增长得分：" + str(result))
    return result


status_score = [0.66, 1.15, 1.71, 2.25, 2.7, 2.96, 3.2, 3.45, 4.01, 4.26, 5.36, 6.70]


def get_basic_status_score(status: int) -> float:
    result = 0
    for i in range(13):
        if status > 0:
            status -= 100
            result += status_score[i] * 100
        else:
            result += status * status_score[i - 1]
            break
    return result


if __name__ == '__main__':
    print(str(get_basic_status_score(1169)))