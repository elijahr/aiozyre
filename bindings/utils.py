from pybindgen.cppclass import MemoryPolicy
from pybindgen.typehandlers.base import PointerParameter, Parameter, ForwardWrapperBase, ReverseWrapperBase, \
    PointerReturnValue


class NULLParameter(Parameter):
    """
    Parameter definition for passing NULL to a function.
    """

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['NULL']

    def convert_c_to_python(self, wrapper):
        raise NotImplementedError

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        wrapper.call_params.append('NULL')


class Unformat(PointerParameter):
    """
    Parameter definition for passing non-format strings to functions which expect format strings + params.

    >>> isinstance(Parameter.new('char*', 's'), Unformat)
    True
    """

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('s', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        if self.default_value is None:
            name = wrapper.declarations.declare_variable(
                self.ctype_no_const, self.name
            )
            wrapper.parse_params.add_parameter('s', ['&' + name], self.value)
        else:
            name = wrapper.declarations.declare_variable(
                self.ctype_no_const, self.name, self.default_value
            )
            wrapper.parse_params.add_parameter(
                's', ['&' + name], self.value, optional=True
            )
        wrapper.call_params.append('"%s"')
        wrapper.call_params.append(name)


class ZyreTPtrPtrParam(PointerParameter):
    """
    Parameter definition for a pointer to a zyre_t pointer
    """
    CTYPES = ['zyre_t**']
    DIRECTIONS = [
        Parameter.DIRECTION_IN,
        Parameter.DIRECTION_OUT,
        Parameter.DIRECTION_INOUT
    ]

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        py_zyre_t_ptr = wrapper.declarations.declare_variable(
            'PyZyre_t*', self.name
        )
        zyre_t_ptr_ptr = wrapper.declarations.declare_variable(
            'zyre_t**', '%s_ptr' % self.name
        )
        wrapper.parse_params.add_parameter(
            'O', ['&' + py_zyre_t_ptr], self.name
        )
        wrapper.before_call.write_code(
            '''{} = &({}->obj);'''.format(zyre_t_ptr_ptr, py_zyre_t_ptr)
        )
        wrapper.call_params.append(zyre_t_ptr_ptr)

    def convert_c_to_python(self, wrapper):
        raise NotImplementedError


class ZmsgTPtrPtrParam(PointerParameter):
    """
    Parameter definition for a pointer to a zmsg_t pointer
    """
    CTYPES = ['zmsg_t**']
    DIRECTIONS = [
        Parameter.DIRECTION_IN,
        Parameter.DIRECTION_OUT,
        Parameter.DIRECTION_INOUT
    ]

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        py_zmsg_t_ptr = wrapper.declarations.declare_variable(
            'PyZmsg_t*', self.name
        )
        zmsg_t_ptr_ptr = wrapper.declarations.declare_variable(
            'zmsg_t**', '%s_ptr' % self.name
        )
        wrapper.parse_params.add_parameter(
            'O', ['&' + py_zmsg_t_ptr], self.name
        )
        wrapper.before_call.write_code(
            '''{} = &({}->obj);'''.format(zmsg_t_ptr_ptr, py_zmsg_t_ptr)
        )
        wrapper.call_params.append(zmsg_t_ptr_ptr)

    def convert_c_to_python(self, wrapper):
        raise NotImplementedError


class ByteStringParam(PointerParameter):
    """
    Parameter definition for C strings which should be translated into Python bytes objects

    >>> from pybindgen import ReturnValue
    >>> isinstance(Parameter.new('PYBYTE*', 'y'), ByteStringParam)
    True
    """
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['PYBYTE*']

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('y', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        if self.default_value is None:
            name = wrapper.declarations.declare_variable(
                self.ctype_no_const, self.name
            )
            wrapper.parse_params.add_parameter('y', ['&' + name], self.value)
        else:
            name = wrapper.declarations.declare_variable(
                self.ctype_no_const, self.name, self.default_value
            )
            wrapper.parse_params.add_parameter(
                'y', ['&' + name], self.value, optional=True
            )
        wrapper.call_params.append(name)


class ByteStringReturn(PointerReturnValue):
    """
    Return value definition for C strings which should be translated into Python bytes objects

    >>> from pybindgen import ReturnValue
    >>> isinstance(ReturnValue.new('PYBYTE*'), ByteStringReturn)
    True
    """
    CTYPES = ['PYBYTE*']

    def get_c_error_return(self):
        return "return NULL;"

    def convert_python_to_c(self, wrapper):
        wrapper.parse_params.add_parameter("y", ['&' + self.value])

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("y", [self.value])


class PtrPtrFreeFunctionPolicy(MemoryPolicy):
    """
    Memory policy for calling destructors that expect a pointer-pointer
    """
    def __init__(self, free_function):
        super(PtrPtrFreeFunctionPolicy, self).__init__()
        self.free_function = free_function

    def get_delete_code(self, cpp_class):
        delete_code = (
            "if (self->obj) {\n"
            "    %s *tmp = self->obj;\n"
            "    self->obj = NULL;\n"
            "    %s(&tmp);\n"
            "}" % (cpp_class.full_name, self.free_function)
        )
        return delete_code

    def __repr__(self):
        return 'cppclass.FreeFunctionPolicyPtrPtr(%r)' % self.free_function
