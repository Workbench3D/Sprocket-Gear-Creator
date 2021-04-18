# Author-Aleksandr Krivosheev
# Description-Sprocket Gear Creator for Russian GOST


import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math
import os.path
import csv

handlers = []


def run(context):
    try:

        # Объявлены переменные, доступные во всем проекте
        global app, ui, mpath, spath
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Переменная ­ путь к файлу параметров модели
        spath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'Resources\config.csv')

        # Создание переменной cmdDef для новой команды
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            'Sprocket',
            'Sprocket Gear Creator', 'Creates a spur gear component',
            'Resources/Sprocket Gear Creator')
        create_panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        create_panel.controls.addCommand(cmd_def)

        # Создание обработчика  события выполнения команды cmdDef
        on_command_created = SprocketHandler()
        cmd_def.commandCreated.add(on_command_created)
        handlers.append(on_command_created)

        # Задание ожидания действий пользователя до завершения модуля
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        create_panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        gear_button = create_panel.controls.itemById('Sprocket')
        if gear_button:
            gear_button.deleteMe()

        cmd_def = ui.commandDefinitions.itemById('Sprocket')
        if cmd_def:
            cmd_def.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class SprocketHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # Обращение к команде, связанной с обработчиком
            cmd = adsk.core.Command.cast(args.command)

            # Обращение к коллекции элементов управления, связанных с 
            # командой
            inputs = cmd.commandInputs

            # Создание формы для указания вида цепи
            typeChain = inputs.addDropDownCommandInput('typeChain',
                                                       'Chain type GOST 13568-97',
                                                       adsk.core.DropDownStyles.TextListDropDownStyle)

            # Чтение в переменную typeChain типа цепи из файла данных
            try:
                with open(spath, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        typeChain.listItems.add(row[0], False, ' ')
            except:
                # Инициализация переменной при ошибке чтения файла
                ui.messageBox('File read error "config.csv"')

            # Создание формы для указания числа зубьев звездочки
            inputs.addStringValueInput(
                'numTeeth', 'Number of sprocket teeth', '20')

            # Создание формы для указания диаметра отверстия
            inputs.addStringValueInput('holeDiam', 'Hole diameter', '10.0')

            # Вывод сообщения об ошибке
            inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)

            # Создание обработчика нажатия кнопки OK в окне генератора
            onExecute = SprocketCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            # Создание обработчика проверки условий
            onValidateInputs = SprocketCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            handlers.append(onValidateInputs)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class SprocketCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:

            # Получение доступа к элементам управления окна генерации 
            # звездочки
            command = args.firingEvent.sender.commandInputs
            hole_diam = command.itemById('holeDiam').value
            num_teeth = command.itemById('numTeeth').value
            type_chain = command.itemById('typeChain').selectedItem.name

            # Получение данных из csv файла
            try:
                with open(spath, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if str(row[0]) == type_chain:
                            step_chain = float(row[1])
                            width_chain = float(row[2])
                            # val_diam = float(row[3])
                            roll_diam = float(row[4])
                            # height_chain = float(row[5])
                        else:
                            continue
            except:
                # Инициализация переменной при ошибке чтения файла
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

            # Запуск функции расчета и построения зведочки
            draw_sprocket(hole_diam, num_teeth, step_chain, width_chain,
                          roll_diam)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Проверка на правильность введенных данных.
class SprocketCommandValidateInputsHandler(
    adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)

            command = args.firingEvent.sender.commandInputs
            num_teeth = command.itemById('numTeeth').value
            hole_diam = command.itemById('holeDiam').value
            type_chain = command.itemById('typeChain').selectedItem
            errMessage = command.itemById('errMessage')

            errMessage.text = ''

            # Проверка на требуемое число зубцов и целое число.
            if not num_teeth.isdigit():
                errMessage.text = 'The number of teeth must be a \
                                whole number.'
                eventArgs.areInputsValid = False
                return
            else:
                num_teeth = int(num_teeth)

            if num_teeth <= 10 or num_teeth > 120:
                errMessage.text = 'Number of sprocket teeth must be \
                                greater than 10 or less than 120.'
                eventArgs.areInputsValid = False
                return

            # Проверка выбран тип цепи
            if type_chain is None:
                errMessage.text = 'Chain type is not selected.'
                eventArgs.areInputsValid = False
                return
            else:
                type_chain = type_chain.name

            # Получение данных из csv файла
            try:
                with open(spath, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if str(row[0]) == type_chain:
                            step_chain = float(row[1])
                            roll_diam = float(row[4])
                        else:
                            continue
            except:
                # Инициализация переменной при ошибке чтения файла
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

            # Диаметр делительной окружно­сти
            pitch_circle_diam = (step_chain / (math.sin(math.radians(180)
                                                        / num_teeth)))

            # Радиус впадин
            hollow_radius = 0.5025 * roll_diam + 0.05

            # Диаметр окружности впадин
            hollow_circle_diam = pitch_circle_diam - 2 * hollow_radius - 0.01

            # Проверка на правильность размеров отверстия
            if float(hole_diam) >= hollow_circle_diam:
                errMessage.text = 'The center hole diameter is too large.'
                eventArgs.areInputsValid = False
                return

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Расчет и построение звездочки
def draw_sprocket(hole_diam, num_teeth, step_chain, width_chain, roll_diam):
    try:

        point = adsk.core.Point3D
        hole_diam = float(hole_diam) / 20
        num_teeth = int(num_teeth)
        pi = math.pi

        def cos(x):
            return math.cos(x)

        def sin(x):
            return math.sin(x)

        def radians(x):
            return math.radians(x)

        # Геометрическая характеристика зацепления
        geometric_characteristic_engagement = step_chain / roll_diam

        # Диаметр делительной окружно­сти
        pitch_circle_diam = (step_chain / (sin(pi / num_teeth)))

        # Диаметр окружности выступов
        if 1.4 <= geometric_characteristic_engagement < 1.5:
            K = 0.48
        elif 1.5 <= geometric_characteristic_engagement < 1.6:
            K = 0.532
        elif 1.6 <= geometric_characteristic_engagement < 1.7:
            K = 0.555
        elif 1.7 <= geometric_characteristic_engagement < 1.8:
            K = 0.575
        elif 1.8 <= geometric_characteristic_engagement < 2.0:
            K = 0.565

        circle_protrusions_diam = (step_chain * (K + 1 / math.tan(pi
                                                                  / num_teeth)))

        # Радиус впадин
        hollow_radius = 0.5025 * roll_diam + 0.05

        # Диаметр окружности впадин
        hollow_circle_diam = pitch_circle_diam - 2 * hollow_radius

        # Наибольшая хорда
        # largest_chord = (pitch_circle_diam*(cos(radians(90)
        #                   /num_teeth)) - 2*hollow_radius)

        # Радиус сопряжения
        fillet_radius = 0.8 * roll_diam + hollow_radius

        # Половина угла впадины
        half_angle_hollow = 55 - 60 / num_teeth

        # Угол сопряжения
        mating_angle = 18 - 56 / num_teeth

        # Половина угла зуба
        half_angle_tooth = 17 - 64 / num_teeth

        # Радиус головки зуба
        # tooth_head_radius = (roll_diam*(1.24
        #                      *(cos(radians(half_angle_tooth))) 
        #                      + 0.8*(cos(radians(mating_angle))) 
        #                      - 1.3025) - 0.05)

        # Прямой участок профиля
        straight_section_profile = (roll_diam * (1.24
                                                 * (sin(radians(half_angle_tooth)))
                                                 - 0.8 * (sin(radians(mating_angle)))))

        # Расстояние от центра дуги впадины до центра дуги головки зуба
        # distance_cavity_arch_tooth = 1.24*roll_diam

        # Координаты точки О1
        point_x_1 = 0.08 * roll_diam * sin(radians(half_angle_hollow))
        point_y_1 = 0.08 * roll_diam * cos(radians(half_angle_hollow))

        # Координаты точки О2
        point_x_2 = 0.124 * roll_diam * cos(pi / num_teeth)
        point_y_2 = 0.124 * roll_diam * sin(pi / num_teeth)

        # Ширина зуба звездочки
        sprocket_tooth_width = 0.093 * width_chain - 0.015

        # Радиус закругления зуба
        tooth_radius = 1.7 * roll_diam

        # Расстояние от вершины зуба до линии центров дуг закруглений
        distance_tooth_curved_arcs = 0.8 * roll_diam

        # Координаты точки A
        # point_x_a = 0	
        point_y_a = hollow_circle_diam / 20

        # Координаты точки O
        # point_x_o = 0	
        point_y_o = pitch_circle_diam / 20

        # Координаты точки E
        point_x_e = (-cos(radians(90 - half_angle_hollow)) * hollow_radius / 10)
        point_y_e = ((hollow_circle_diam / 2 + hollow_radius
                      - sin(radians(90 - half_angle_hollow))
                      * hollow_radius) / 10)

        # Координаты точки O1
        point_x_o1 = point_x_1
        point_y_o1 = point_y_1 + pitch_circle_diam / 20

        # Координаты точки F
        point_x_f = (-cos(radians(90 - mating_angle
                                  - half_angle_hollow)) * fillet_radius / 10 + point_x_o1)
        point_y_f = (pitch_circle_diam / 20 + point_y_1
                     - sin(radians(90 - mating_angle
                                   - half_angle_hollow)) * fillet_radius / 10)

        # Координаты точки G
        point_x_g = (-sin(radians(180 / num_teeth + half_angle_tooth))
                     * straight_section_profile / 10 + point_x_f)
        point_y_g = (cos(radians(180 / num_teeth + half_angle_tooth))
                     * straight_section_profile / 10 + point_y_f)

        # Координаты точки O2
        point_x_o2 = -point_x_2
        point_y_o2 = pitch_circle_diam / 20 - point_y_2

        # Координаты точки B
        point_x_b = (-sin(radians(180 / num_teeth)) * circle_protrusions_diam / 20)
        point_y_b = (cos(radians(180 / num_teeth)) * circle_protrusions_diam / 20)

        # Координаты точки C
        point_x_c = (-sin(radians(180 / num_teeth)) * hollow_circle_diam / 20)
        point_y_c = (cos(radians(180 / num_teeth)) * hollow_circle_diam / 20)

        # Получение доступа к корневому компоненту модели           
        design = app.activeProduct
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        rootComp = design.rootComponent

        # Выбор типа операции вращение, выдавливание и тд.
        operation = adsk.fusion.FeatureOperations

        # Создание переменной для коллекции эскизов модели
        sketches = rootComp.sketches

        # Создание эскиза на плоскости XY
        Sketch1 = sketches.add(rootComp.xYConstructionPlane)

        # Получение доступа к эскизным объектам типа 'окружность'            
        circles = Sketch1.sketchCurves.sketchCircles

        # Создание эскизной окружности впадин
        circles.addByCenterRadius(point.create(0, 0, 0),
                                  hollow_circle_diam / 20.0)

        # Создание эскизной окружно­сти отверстия
        circles.addByCenterRadius(point.create(0, 0, 0), hole_diam)

        # Сохранение эскизной окружности как первого профиля
        profile1 = Sketch1.profiles.item(0)

        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(profile1,
                                        operation.NewBodyFeatureOperation)

        # Выдавливание окружности на ширину зуба звездочки 
        distance = adsk.core.ValueInput.createByReal(sprocket_tooth_width)
        extInput.setDistanceExtent(False, distance)

        # Создание выдавливания
        baseExtrude = extrudes.add(extInput)

        # Создание эскиза на плоскости XY
        Sketch2 = sketches.add(rootComp.xYConstructionPlane)

        # Получение доступа к эскизным объектам типа 'окружность', 
        # 'дуга', 'линия'            
        # circles = Sketch2.sketchCurves.sketchCircles
        arcs = Sketch2.sketchCurves.sketchArcs
        lines = Sketch2.sketchCurves.sketchLines

        # Дуга AE
        arcs.addByCenterStartSweep(point.create(0, point_y_o, 0),
                                   point.create(0, point_y_a, 0),
                                   -pi * half_angle_hollow / 180)

        # Дуга EF
        arcs.addByCenterStartSweep(point.create(point_x_o1, point_y_o1, 0),
                                   point.create(point_x_e, point_y_e, 0),
                                   -pi * mating_angle / 180)

        # Линия FG
        lines.addByTwoPoints(point.create(point_x_f, point_y_f, 0),
                             point.create(point_x_g, point_y_g, 0))

        # Дуга GK
        arcs.addByCenterStartSweep(point.create(point_x_o2, point_y_o2, 0),
                                   point.create(point_x_g, point_y_g, 0),
                                   pi * 40 / 180)

        # Дуга BK
        arcs.addByCenterStartSweep(point.create(0, 0, 0),
                                   point.create(point_x_b, point_y_b, 0),
                                   -pi / (num_teeth * 2))

        # Дуга AC
        arcs.addByCenterStartSweep(point.create(0, 0, 0),
                                   point.create(0, point_y_a, 0),
                                   pi / num_teeth)

        # Линия BC
        lines.addByTwoPoints(point.create(point_x_b, point_y_b, 0),
                             point.create(point_x_c, point_y_c, 0))

        # Сохранение эскизной окружности как первого профиля
        profile2 = Sketch2.profiles.item(0)

        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(profile2,
                                        operation.JoinFeatureOperation)

        # Выдавливание профиля зуба на ширину зуба звездочки.
        distance = adsk.core.ValueInput.createByReal(sprocket_tooth_width)
        extInput.setDistanceExtent(False, distance)

        # Создание выдавливания.
        toothExtrude_1 = extrudes.add(extInput)

        # Создание эскиза на плоскости XY
        Sketch3 = sketches.add(rootComp.xYConstructionPlane)

        # Получение доступа к эскизным объектам типа 'окружность', 
        # 'дуга', 'линия'            
        # circles = Sketch3.sketchCurves.sketchCircles
        arcs = Sketch3.sketchCurves.sketchArcs
        lines = Sketch3.sketchCurves.sketchLines

        # Создаем зеркальный эскиз
        # Дуга -AE
        arcs.addByCenterStartSweep(point.create(0, point_y_o, 0),
                                   point.create(0, point_y_a, 0),
                                   pi * half_angle_hollow / 180)

        # Дуга -EF
        arcs.addByCenterStartSweep(point.create(-point_x_o1, point_y_o1, 0),
                                   point.create(-point_x_e, point_y_e, 0),
                                   pi * mating_angle / 180)

        # Линия -FG
        lines.addByTwoPoints(point.create(-point_x_f, point_y_f, 0),
                             point.create(-point_x_g, point_y_g, 0))

        # Дуга -GK
        arcs.addByCenterStartSweep(point.create(-point_x_o2, point_y_o2, 0),
                                   point.create(-point_x_g, point_y_g, 0),
                                   -pi * 40 / 180)

        # Дуга -BK
        arcs.addByCenterStartSweep(point.create(0, 0, 0),
                                   point.create(-point_x_b, point_y_b, 0),
                                   pi / (num_teeth * 2))

        # Дуга -AC
        arcs.addByCenterStartSweep(point.create(0, 0, 0),
                                   point.create(0, point_y_a, 0),
                                   -pi / num_teeth)

        # Линия -BC
        lines.addByTwoPoints(point.create(-point_x_b, point_y_b, 0),
                             point.create(-point_x_c, point_y_c, 0))

        # Сохранение эскизной окружности как первого профиля
        profile3 = Sketch3.profiles.item(0)

        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(profile3,
                                        operation.JoinFeatureOperation)

        # Выдавливание профиля зуба на ширину зуба звездочки
        distance = adsk.core.ValueInput.createByReal(sprocket_tooth_width)
        extInput.setDistanceExtent(False, distance)

        # Создание выдавливания
        toothExtrude_2 = extrudes.add(extInput)

        # Вызываем опирацию массив вращения
        circularPatterns = rootComp.features.circularPatternFeatures
        entities = adsk.core.ObjectCollection.create()
        entities.add(toothExtrude_1)
        entities.add(toothExtrude_2)
        cylFace = baseExtrude.sideFaces.item(0)
        patternInput = circularPatterns.createInput(entities, cylFace)
        numTeethInput = adsk.core.ValueInput.createByString(str(num_teeth))
        patternInput.quantity = numTeethInput
        circularPatterns.add(patternInput)

        # Создание эскиза на плоскости YZ
        Sketch4 = sketches.add(rootComp.yZConstructionPlane)

        # Получение доступа к эскизным объектам типа 'дуга', 'линия'            
        arcs = Sketch4.sketchCurves.sketchArcs
        lines = Sketch4.sketchCurves.sketchLines

        # Создание эскиза
        # Дуги
        point_1_ap = (circle_protrusions_diam / 20
                      - distance_tooth_curved_arcs / 10)
        point_2_ap = tooth_radius / 10 - sprocket_tooth_width
        point_1_ap_steps = point_1_ap + tooth_radius / 10

        # Угол дуги 
        arc_angle = (math.degrees(math.acos(10
                                            * (tooth_radius / 10 - sprocket_tooth_width / 2 - 0.01)
                                            / tooth_radius)))

        arcs.addByCenterStartSweep(
            point.create(-tooth_radius / 10, point_1_ap, 0),
            point.create(0, point_1_ap, 0),
            pi * arc_angle / 180)
        arcs.addByCenterStartSweep(
            point.create(point_2_ap, point_1_ap, 0),
            point.create(-sprocket_tooth_width - 0.0001, point_1_ap, 0),
            -pi * arc_angle / 180)

        # Линии
        lines.addByTwoPoints(point.create(0, point_1_ap, 0),
                             point.create(0, point_1_ap_steps, 0))
        lines.addByTwoPoints(
            point.create(-sprocket_tooth_width - 0.0001, point_1_ap, 0),
            point.create(-sprocket_tooth_width - 0.0001, point_1_ap_steps, 0))
        lines.addByTwoPoints(
            point.create(0, point_1_ap_steps, 0),
            point.create(-sprocket_tooth_width - 0.0001, point_1_ap_steps, 0))

        # Осевая линия
        AxisLine = lines.addByTwoPoints(
            point.create(0, 0, 0),
            point.create(-sprocket_tooth_width - 0.0001, 0, 0))

        # Сохранение эскизной окружности как профиля
        prof = Sketch4.profiles.item(0)

        # Создание операции вырез вращением
        revolves = rootComp.features.revolveFeatures
        revInput = revolves.createInput(prof,
                                        AxisLine,
                                        operation.CutFeatureOperation)

        # Указание дистанции вращения
        # Вращение осуществить на полный оборот
        angle = adsk.core.ValueInput.createByReal(2 * pi)
        revInput.setAngleExtent(False, angle)

        # Создание вращения
        revolves.add(revInput)

    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
