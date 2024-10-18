from math import exp
import numpy
from single_voltage_irradiance_dependence import SingleVoltageIrradianceDependence


class SingleDiodeModel(object):
    boltzmann_constant = 1.38065e-23
    charge_of_electron = 1.602e-19
    nominal_temperature = 25 + 273
    nominal_irradiance = 1000
    band_gap = 1.12  # Silício a 25 graus Celsius

    '''
    temperature_voltage_coefficient [V/ºC] not [%/ºC]
    temperature_current_coefficient [A/ºC] not [%/ºC]
    '''

    def __init__(self,
                 short_circuit_current,
                 open_circuit_voltage,
                 number_of_cells_in_series,
                 number_of_voltage_decimal_digits=1,
                 temperature_voltage_coefficient=-0.123,
                 temperature_current_coefficient=0.0032,
                 series_resistance=0.221,
                 shunt_resistance=415.405,
                 diode_quality_factor=1.3):

        self.number_of_voltage_decimal_digits = number_of_voltage_decimal_digits

        self.short_circuit_current = self.__convert_to_float(short_circuit_current)
        # Certifique-se de que a tensão tenha o número especificado de casas decimais:
        self.open_circuit_voltage = round(self.__convert_to_float(open_circuit_voltage),
                                          self.number_of_voltage_decimal_digits)
        self.number_of_cells_in_series = number_of_cells_in_series
        self.temperature_voltage_coefficient = temperature_voltage_coefficient
        self.temperature_current_coefficient = temperature_current_coefficient
        self.series_resistance = series_resistance
        self.shunt_resistance = shunt_resistance
        self.diode_quality_factor = diode_quality_factor

    def calculate(self, operating_temperature, actual_irradiance):

        nominal_thermal_voltage = self.__thermal_voltage(self.nominal_temperature)
        operating_thermal_voltage = self.__thermal_voltage(operating_temperature)

        nominal_saturation_current = self.__saturation_current(self.nominal_temperature, nominal_thermal_voltage)
        saturation_current = self.__saturation_current(operating_temperature, operating_thermal_voltage)

        actual_short_circuit_current = self.__actual_current(self.short_circuit_current, operating_temperature,
                                                             actual_irradiance)

        photo_current = actual_short_circuit_current

        actual_open_circuit_voltage = round(
            self.__actual_voltage(photo_current, nominal_saturation_current, nominal_thermal_voltage,
                                  self.open_circuit_voltage, operating_temperature),
            self.number_of_voltage_decimal_digits)

        # Certifique-se de levar em conta o número de casas decimais:
        number_of_elements = int(actual_open_circuit_voltage * 10 ** self.number_of_voltage_decimal_digits) + 1

        self.voltages = numpy.linspace(0., actual_open_circuit_voltage, number_of_elements)
        self.currents = numpy.zeros((1, number_of_elements)).flatten()
        self.powers = numpy.zeros((1, number_of_elements)).flatten()

        self.currents[0] = actual_short_circuit_current

        # O último elemento da corrente não se torna 0 com base no cálculo iterativo abaixo.
        # Portanto, o loop for abaixo é interrompido no elemento anterior ao último.
        # Assim, o valor do último elemento de corrente permanece 0[A] e também o último elemento de potência permanece 0[W].
        for i in range(1, number_of_elements - 1):
            calculated_current = self.__current(self.voltages[i], self.currents[i - 1], photo_current,
                                                saturation_current, operating_thermal_voltage)
            # Nota: O seguinte é um ajuste rápido para evitar corrente negativa em MultipleModulesSingleDiodeModel
            #       quando se usa series_resistance, shunt_resistance, and diode_quality_factor para nominal_irradiance no caso de sombreamento parcial..
            # TODO: Modificar para calcular esses valores com base na irradiância sob sombreamento parcial usando root_finding.
            if calculated_current < 0.0:
                calculated_current = 0.0
            self.currents[i] = calculated_current

            self.powers[i] = self.voltages[i] * self.currents[i]

    def __convert_to_float(self, value):
        if isinstance(value, float):
            return value
        else:
            return float(value)

    def __thermal_voltage(self, temperature):
        # Baseado na equação (2) de [1], que inclui o fator de qualidade do diodo e não inclui o número de células em série:
        return (self.diode_quality_factor * self.boltzmann_constant * temperature) / self.charge_of_electron

    def __nominal_saturation_current(self, thermal_voltage):
        # O seguinte é baseado na equação (6) de [2], mas a tensão térmica é definida como a equação (2) de [1], que inclui o fator de qualidade do diodo e não inclui o número de células em série, e assim a seguinte equação é modificada de acordo:
        return self.short_circuit_current / (
                exp(self.open_circuit_voltage / (self.number_of_cells_in_series * thermal_voltage)) - 1)

    def __saturation_current(self, operating_temperature, thermal_voltage):
        # O seguinte é baseado na equação (7) de [2], mas a tensão térmica é definida como a equação (2) de [1], que inclui o fator de qualidade do diodo e não inclui o número de células em série, e assim a seguinte equação é modificada de acordo:
        return (self.short_circuit_current + self.temperature_current_coefficient * (
                operating_temperature - self.nominal_temperature)) / (exp((
                                                                                  self.open_circuit_voltage + self.temperature_voltage_coefficient * (
                                                                                  operating_temperature - self.nominal_temperature)) / (
                                                                                  self.number_of_cells_in_series * thermal_voltage)) - 1)

    def __current(self, voltage, current, photo_current, saturation_current, operating_thermal_voltage):
        # Baseado na equação (1) de [1] (a tensão térmica é definida como a equação (2) de [1], que inclui o fator de qualidade do diodo e não inclui o número de células em série):
        return photo_current - saturation_current * (exp((voltage + current * self.series_resistance) / (
                self.number_of_cells_in_series * operating_thermal_voltage)) - 1) - (
                (voltage + current * self.series_resistance) / self.shunt_resistance)

    def __actual_current(self, nominal_current, operating_temperature, actual_irradiance):
        # Baseado na equação (4) de [2], que usa [A/ºC] como unidade do coeficiente de temperatura da corrente (Nota: Alguns datasheets usam [%/ºC] como unidade):
        return (actual_irradiance / self.nominal_irradiance) * (
                nominal_current + self.temperature_current_coefficient * (
                operating_temperature - self.nominal_temperature))

    def __actual_voltage(self, photo_current, saturation_current, nominal_thermal_voltage, nominal_voltage,
                         operating_temperature):
        # TODO: A curva I-V e a curva P-V têm uma queda acentuada perto da tensão de circuito aberto quando a dependência de irradiância é levada em conta
        # Dependência da irradiância:
        single_voltage_irradiance_dependence = SingleVoltageIrradianceDependence(photo_current,
                                                                                 saturation_current,
                                                                                 self.shunt_resistance,
                                                                                 self.number_of_cells_in_series,
                                                                                 nominal_thermal_voltage)
        irradiance_dependent_voltage = single_voltage_irradiance_dependence.calculate(nominal_voltage)

        # Dependência da temperatura:
        # Baseado na equação (24) de [1], mas levando em conta que a unidade do coeficiente de temperatura da tensão é [V/ºC] em vez de [%/ºC]. (Nota: Diferentes datasheets usam uma ou outra dessas unidades):
        return irradiance_dependent_voltage + self.temperature_voltage_coefficient * (
                operating_temperature - self.nominal_temperature)
