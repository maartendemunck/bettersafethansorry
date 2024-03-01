from bettersafethansorry.actions.archive import ArchiveFiles


class ArchiveMinecraftServerJavaEdition(ArchiveFiles):

    required_keys = [
        'source-container'
    ]

    optional_keys = {
    }

    def __init__(self, action_config, logger, extra_required_keys=[], extra_optional_keys={}):
        required_keys = [*ArchiveMinecraftServerJavaEdition.required_keys, *extra_required_keys]
        optional_keys = {**ArchiveMinecraftServerJavaEdition.optional_keys, **extra_optional_keys}
        if 'source-directory' not in action_config:
            # Use default location in https://github.com/itzg/docker-minecraft-server by default.
            action_config['source-directory'] = '/data'
        super().__init__(action_config, logger, required_keys, optional_keys)

    def _compose_base_pre_archive_commands(self, use_shell):
        rcon_save_off_cmd = ['rcon-cli', 'save-off']
        rcon_save_all_cmd = ['rcon-cli', 'save-all']
        sleep_cmd = ['sleep', '5']
        return [rcon_save_off_cmd if use_shell is False else self._convert_command_to_string(rcon_save_off_cmd),
                rcon_save_all_cmd if use_shell is False else self._convert_command_to_string(rcon_save_all_cmd),
                sleep_cmd if use_shell is False else self._convert_command_to_string(sleep_cmd)]
    
    def _compose_base_post_archive_commands(self, use_shell):
        rcon_save_on_cmd = ['rcon-cli', 'save-on']
        return [rcon_save_on_cmd if use_shell is False else self._convert_command_to_string(rcon_save_on_cmd)]

