from lib.vsys import VSys

class Sys2(VSys):
  sys_prompt = sys_prime + """
S2-Coord: AlgedonicSignal,Pain/Pleasure,Amount+How.
Analize which system is this message for. What information it needs. Which messages are more relevant according to source system + pain/pleasure signal + content relevance. Keep only most relevant messages.
"""

  def step(self, from_list, to):
    self.conversation.append( usermsg(to.state()) )

    for from_sys in from_list:
      self.conversation.append( usermsg(from_sys.state()) )

    return super().step()