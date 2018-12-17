import json
from controller import AlienwareController as AC
from random import randint
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')


def generateRandomColor():
    return [randint(0, 255), randint(0, 255), randint(0, 255)]


class AlienwareTheme:
    def __init__(self, filepath):
        with open(filepath) as file:
            jsonString = ''.join(file.readlines())
        self.theme = json.loads(jsonString)

    def validate(self):
        t = self.theme
        validatedTempo = t.get('TEMPO', 200)
        validatedDuration = t.get('DURATION', 10000)
        validatedZoneCodeSequenceMap = {}

        zones = t.get('ZONES', {})
        for name, zoneCode in AC.Zones.CODES.items():
            sequence = zones.get(name, [])
            validatedSequence = []
            for effect in sequence:
                effectName = effect.get('EFFECT', '')
                if effectName not in [AC.Commands.SET_COLOR, AC.Commands.BLINK_COLOR, AC.Commands.MORPH_COLOR,
                                      AC.Commands.LOOP_SEQUENCE]:
                    continue
                if effectName == AC.Commands.SET_COLOR or effectName == AC.Commands.BLINK_COLOR:
                    effect['COLOR'] = effect.get('COLOR', generateRandomColor())
                elif effectName == AC.Commands.MORPH_COLOR:
                    effect['COLOR1'] = effect.get('COLOR1', generateRandomColor())
                    effect['COLOR2'] = effect.get('COLOR2', generateRandomColor())
                validatedSequence.append(effect)
            validatedZoneCodeSequenceMap[zoneCode] = validatedSequence

        logging.debug('Theme validation complete')
        logging.debug('Validated tempo = {}ms, Validated duration = {}ms'.format(validatedTempo, validatedDuration))
        logging.debug('Validated zone sequence map:'.format(validatedZoneCodeSequenceMap))

        return validatedTempo, validatedDuration, validatedZoneCodeSequenceMap

    def apply(self):
        validatedTempo, validatedDuration, validatedZoneCodeSequenceMap = self.validate()

        ac = AC()
        try:
            ac.driver.acquire()

            ac.reset(AC.Reset.CODES[AC.Reset.ALL_LIGHTS_ON])
            ac.waitUntilControllerReady()

            commands = [ac.makeSetTempoCmd(validatedTempo)]
            sequenceId = 0
            for zoneCode, sequence in validatedZoneCodeSequenceMap.items():
                for effect in sequence:
                    effectName = effect['EFFECT']
                    print(effectName)
                    if effectName == AC.Commands.SET_COLOR:
                        commands.append(ac.makeSetColorCmd(sequenceId, zoneCode, effect['COLOR']))
                    elif effectName == AC.Commands.BLINK_COLOR:
                        commands.append(ac.makeBlinkColorCmd(sequenceId, zoneCode, effect['COLOR']))
                    elif effectName == AC.Commands.MORPH_COLOR:
                        commands.append(ac.makeMorphColorCmd(sequenceId, zoneCode, effect['COLOR1'], effect['COLOR2']))
                    elif effectName == AC.Commands.LOOP_SEQUENCE:
                        commands.append(ac.makeLoopSequenceCmd())
                    else:
                        raise RuntimeError('Invalid effect code')
                sequenceId += 1
            commands.append(ac.makeExecuteCmd())

            ac.sendCommands(commands)

            ac.waitUntilControllerReady()
        except Exception as e:
            logging.error('Exception occurred', exc_info=True)
        finally:
            ac.driver.release()

    def __str__(self):
        return str(self.theme)


theme = AlienwareTheme("themes/moon.json")
theme.apply()
